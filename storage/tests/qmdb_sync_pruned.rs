//! Explicit wire checks for the pruning response shared by MMR and MMB sync.
#![cfg(feature = "std")]

use commonware_codec::{Copying, Decode as _, Encode as _, EncodeSize as _};
use commonware_cryptography::sha256::Digest as Sha256Digest;
use commonware_storage::{
    merkle::{Family, Location, mmb, mmr},
    qmdb::sync::Response,
};

fn check_pruned_response_codec<F: Family>() {
    for value in [0, 127, 128, 16_384, F::MAX_LEAVES.as_u64()] {
        let frontier = Location::<F>::new(value);
        let response = Response::<F, u64, Sha256Digest>::Pruned { frontier };
        let encoded = response.encode();
        assert_eq!(encoded[0], 2);
        assert_eq!(encoded.len(), response.encode_size());
        assert_eq!(&encoded[1..], frontier.encode().as_ref());
        if value == 128 {
            assert_eq!(encoded.as_ref(), &[2, 0x80, 0x01]);
        }

        let decoded = Response::<F, u64, Sha256Digest>::decode_cfg(encoded.clone(), &(0, ()))
            .expect("pruned response must roundtrip without an operation budget");
        assert!(matches!(decoded, Response::Pruned { frontier: actual } if actual == frontier));

        // Every incomplete frontier, including a tag-only frame, must fail decoding.
        for len in 0..encoded.len() {
            assert!(
                Response::<F, u64, Sha256Digest>::decode_cfg(Copying(&encoded[..len]), &(0, ()))
                    .is_err()
            );
        }
    }

    let invalid = Response::<F, u64, Sha256Digest>::Pruned {
        frontier: Location::new(F::MAX_LEAVES.as_u64() + 1),
    };
    assert!(Response::<F, u64, Sha256Digest>::decode_cfg(invalid.encode(), &(0, ())).is_err());
}

#[test]
fn test_pruned_response_codec_mmr() {
    check_pruned_response_codec::<mmr::Family>();
}

#[test]
fn test_pruned_response_codec_mmb() {
    check_pruned_response_codec::<mmb::Family>();
}
