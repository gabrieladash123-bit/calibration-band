# CalibrationBand

**Category** · Intelligent Contracts

CalibrationBand converts scored benchmark evidence into a monotone calibration curve. It helps builders quantify how unresolved cases affect an ordered score's observed success rate.

The leader and each validator independently fetch the full commit-pinned report, verify its SHA-256 digest, and classify every case as pass, fail, or unknown against the same criterion. Consensus requires exact agreement on the normalized case IDs, scores, and outcomes. The contract uses those labels to compute the lowest and highest isotonic fits across possible resolutions of the unknown cases. It publishes the exact bounds, pooling blocks, and case-level outcomes in one immutable write.

The synthetic StudioNet example asks whether a saved payload was recovered intact after a restart. Scores 20 and 50 share a calibrated range of 3/8 to 5/8. Score 80 has an exact fitted value of 3/4. The range describes uncertainty in those benchmark labels. GenVM lint and the direct test suite passed. The deployment, fit, and expected duplicate rejection finalized with validator majorities and were replayed through public RPC.

- **Repository** · [Source, tests, and documentation](https://github.com/gabrieladash123-bit/calibration-band)
- **StudioNet Explorer** · [Deployed contract](https://explorer-studio.genlayer.com/address/0x59b99946Facc77971d268D390170C917Ad9C4219)
- **Proofs** · [Finalized receipts and exact onchain readback](https://github.com/gabrieladash123-bit/calibration-band/blob/main/proofs/studionet.json)
