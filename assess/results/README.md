# Assessment results (A4, 2026-11-08)

Trees: OpenTitan master 7d46c64, core-v-verif master b137fd2 (ivpm dep-set `assess`).
Produced from the repo root with `packages/python/bin` on PATH:

```sh
OT=packages/opentitan/hw
python assess/scan.py $OT/dv/sv $OT/ip $OT/top_earlgrey -o assess/results/ot_scan.json
C=packages/core-v-verif
python assess/scan.py $C/lib/uvm_agents $C/lib/uvm_libs $C/lib/uvm_components \
    $C/lib/cv_dv_utils/uvm $C/cv32e40p/env $C/cv32e40s/env $C/cv32e40x/env \
    -o assess/results/cv_scan.json
for t in ot cv; do
  python assess/gaps.py --scan assess/results/${t}_scan.json -o assess/results/${t}_gaps.json
  python assess/gaps.py --scan assess/results/${t}_scan.json --text --rel packages > assess/results/${t}_gaps.txt
  python assess/size.py --scan assess/results/${t}_scan.json -o assess/results/${t}_size.json
  python assess/size.py --scan assess/results/${t}_scan.json --text > assess/results/${t}_size.txt
done
```

Only `top_earlgrey` is scanned: `top_darjeeling` and `top_englishbreakfast` hold generated
copies of the same `ip_autogen` envs and would double-count.

## Scan

| tree | files | classes | data items | data objects |
|---|---|---|---|---|
| OpenTitan | 2708 | 1339 | 47 | 113 |
| core-v-verif | 565 | 462 | 40 | 63 |

## Gaps (rules G1-G6, see `assess/gaps.py`)

| tree | kind | G1 | G2 | G3 | G4 | G5 |
|---|---|---|---|---|---|---|
| OT | item | 89 | 96 | 59 | 0 | 3 |
| OT | object | 613 | 1 | 0 | 3 | 50 |
| cv | item | 25 | 1 | 0 | 8 | 2 |
| cv | object | 62 | 0 | 0 | 0 | 4 |

Headline = findings on `item` classes plus objects whose name matches txn/trn/item.
OT: 22 classes, 248 findings; cv: ~20 classes. The other object findings (OT 666, cv ~70)
are mostly `*_cfg`, `*_cntxt` and utility classes (entropy_src_dut_cfg 86, csrng_env_cfg 75,
aes_env_cfg 58, ...): config is shared by handle and rarely copied, so G1 there is
informational (all such findings hand-checked in A2 were false positives).

### Top headline classes, hand verdicts

TP = real gap, LOW = real but small impact, FP = intended.

OpenTitan

| class | findings | verdict |
|---|---|---|
| aes_message_item (hw/ip/aes) | G1 18, G2 37, G3 27 | TP: hand do_copy of 37 members, no do_compare (compare() sees none). G1 mostly rand knobs (pct/weights, LOW) but `fixed_key`/`fixed_iv` not copied while `fixed_key_en` is (TP). |
| aes_seq_item | G1 8, G2 18, G3 13 | TP: do_compare covers a subset; `valid`, `data_out_vld` not copied. |
| usb20_item (dv/sv) | G2 15, G3 15 | TP: do_copy only (A2). |
| spi_transaction_item (spi_host) | G1 23 | TP: do_copy copies no members, and calls `` `downcast(rhs, rhs_)`` with the arguments reversed (ext, base); copy() drops `cmd` and `segments`. |
| rv_dm_mode_seq_item | G1 20 | TP: only do_print; copy() loses all 20 members. |
| spi_segment_item | G1 3, G2 9, G3 4 | TP: no do_compare; G1 are rand knobs (LOW). |
| csrng_item (dv/sv) | G2 8 | TP: no do_compare (A2). |
| jtag_item | G1 7 | LOW: stimulus knobs (A2). |
| racl_error_log_item | G2 5 | TP: do_copy + do_print, no do_compare. |
| dma_seq_item | G1 3 | LOW: derived flags `valid_dma_config`, `*_addr_in_range` not registered. |
| entropy_src_xht_item, flash_phy_prim_item | G5 | TP: data members, no automation. |
| kmac_app_req_item.m_delay, key_sideload_item.m_stop_requested | G2/G1 | FP: deliberate (A2). |

core-v-verif

| class | findings | verdict |
|---|---|---|
| memory_txn (cv_dv_utils memory_rsp_model) | G1 8 | TP: only 2 timing fields registered (A2). |
| axi_superset_txn_c | G1 5 | TP: error-injection/atomic fields; `name` FP (A2). |
| uvma_axi_transaction_c (axi5) | G1 5 | not hand-checked |
| uvma_rvfi_csr_seq_item_c | G1 2, G4 1 | TP (A2). |
| uvma_obi_memory_mon_trn_c | G1 2 | TP: `exokay` (A2). |
| uvma_cvxif_req/resp_item_c | G5 | TP: rand members, no automation (A2). |
| uvma_*_seq_item_c (rvvi, rvfi, fencei, isacov) | G4 x8 | LOW: convert2string/do_* without super. |
| uvml_trn_seq_item_c.__uid | G1 | FP (A2). |

Hand-check totals (A2 + A4): OT items 14 classes checked, 10 TP, 2 LOW, 2 FP.
Transaction classes are mostly real gaps; cfg/cntxt findings are mostly not.

## Size (data classes, `assess/size.py`, depth 1)

| root | classes | field macros | hand do_* lines | sv-weave lines | saved src | expanded macro lines | woven (est.) |
|---|---|---|---|---|---|---|---|
| OT hw/dv/sv | 54 | 371 | 395 | 85 | 681 | 50643 | 7740 |
| OT hw/ip | 43 | 171 | 635 | 36 | 770 | 21706 | 11145 |
| OT top_earlgrey | 6 | 18 | 0 | 6 | 12 | 2078 | 915 |
| cv lib/uvm_agents | 61 | 723 | 352 | 231 | 844 | 103719 | 9435 |
| cv lib/uvm_libs | 5 | 43 | 0 | 25 | 18 | 5295 | 555 |
| cv lib/cv_dv_utils/uvm | 13 | 119 | 162 | 60 | 221 | 17161 | 1815 |
| cv cv32e40{p,s,x}/env | 9 | 101 | 22 | 12 | 111 | 17499 | 1110 |

Totals: OT 103 classes, ~1463 source lines saved, ~74k expanded macro lines replaced by
~20k woven lines (estimate). core-v-verif 88 classes, ~1194 saved, ~144k expanded vs ~13k woven.
`saved` is an upper bound (hand do_* methods with non-field logic would partly stay);
`weave` counts one attribute per field with UVM_NO*/radix flags. Per-group tables are in
`*_size.txt`. Biggest hand-code groups: aes 174, kmac_app_agent 166, isacov 141 (hand),
axi_superset 105, entropy_src 115.

## Files

- `*_scan.json` scanner output (classes, members, methods), input to the other two.
- `*_gaps.json`, `*_gaps.txt` findings (one line each in the .txt).
- `*_size.json`, `*_size.txt` size estimate per class / group / root.
