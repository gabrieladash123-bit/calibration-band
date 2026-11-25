# CalibrationBand

CalibrationBand publishes a monotone calibration curve for ordered benchmark scores. GenLayer validators independently read a pinned benchmark report and determine which cases demonstrate the required outcome. Unknown outcomes widen the band.

[Contract source](contracts/calibration_band.py) · [Example report](fixtures/restoration.json) · [StudioNet proof](#studionet-proof) · [Submission text](SUBMISSION.md)

## Example

The synthetic benchmark asks whether each saved payload survived a service restart. Raw pass rates at scores 20 and 50 violate the assumed score ordering, so isotonic regression pools those adjacent scores.

| Score | Pass | Fail | Unknown | Calibrated range |
| ---: | ---: | ---: | ---: | --- |
| 20 | 3 | 1 | 0 | 3/8–5/8 |
| 50 | 0 | 2 | 2 | 3/8–5/8 |
| 80 | 3 | 1 | 0 | 3/4 |

## Consensus and storage

1. `fit(source, digest, criterion)` binds a full Git commit coordinate, SHA-256 digest, and outcome criterion.
2. The leader and each validator independently fetch the full report, verify its bytes, and classify the evidence for every case. Every normalized case ID, score, and outcome must match exactly.
3. The contract runs the pool-adjacent-violators algorithm twice, assigning every unknown to failure for the lower fit and to success for the upper fit. Every completion lies between those fits because each isotonic fitted value is monotone in the input labels.
4. A single write publishes the immutable result, including adjudicated labels, bin counts, and both sets of exact pooling blocks. The full fit is readable through `get_fit(fit_id)`. `get_point(fit_id, score)` returns the range at an observed score.

The band quantifies unresolved labels in the committed report. Its coverage is conditional on the benchmark cases, the outcome criterion, and consensus adjudication. A consumer should choose benchmarks with provenance and representative samples for its use case.

## Input and verification

Use a public `owner/repo/commit/path.json` coordinate with a full commit and a lowercase SHA-256 digest of the original UTF-8 bytes. The report has 4–32 cases with unique IDs, integer scores from 0 to 100, and prose notes. It must contain at least two distinct scores and fit within 6,144 bytes.

```sh
python -m pip install -r requirements-dev.txt
genvm-lint download --version v0.2.16
genvm-lint check contracts/calibration_band.py
python -m pytest tests/direct -q
```

The direct tests replay validator disagreement and changed source bytes. An independent min–max implementation checks each partial label vector in a four-case benchmark against every binary completion.

## StudioNet proof

The deployment, benchmark fit, and expected duplicate rejection all finalized with 3 of 5 votes. Replay verifies the deployed source, the twelve recorded outcomes, the pooling blocks, and the lookup results for an observed and an unobserved score.

[Deployed contract](https://explorer-studio.genlayer.com/address/0x59b99946Facc77971d268D390170C917Ad9C4219) · [Proof ledger](proofs/studionet.json) · [GenVM checks](https://github.com/gabrieladash123-bit/calibration-band/actions/runs/45685160406)

```sh
npm ci
npm run verify
```
