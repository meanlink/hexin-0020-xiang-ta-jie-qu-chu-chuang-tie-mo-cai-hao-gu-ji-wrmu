CREATE TABLE IF NOT EXISTS cut_withdrawals (
    receipt_sheet_id uuid NOT NULL REFERENCES cut_receipts(sheet_id),
    withdrawn_sheet_id uuid NOT NULL REFERENCES cut_sheets(id),
    withdrawn_order bigint NOT NULL,
    released_reserve_mm integer NOT NULL CHECK (released_reserve_mm > 0),
    PRIMARY KEY (receipt_sheet_id, withdrawn_sheet_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS one_withdrawal_per_sheet ON cut_withdrawals (withdrawn_sheet_id);
