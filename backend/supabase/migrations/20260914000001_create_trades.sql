-- Journal of trades taken. current_price is marked by the open-trade CMP job.
CREATE TABLE trades (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker text NOT NULL,
    name text NOT NULL,
    side text NOT NULL DEFAULT 'long'
        CHECK (side IN ('long', 'short')),
    status text NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'closed')),
    entry_price numeric NOT NULL CHECK (entry_price > 0),
    quantity int NOT NULL CHECK (quantity > 0),
    stop_loss numeric,
    take_profit numeric,
    current_price numeric CHECK (current_price IS NULL OR current_price > 0),
    opened_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz,
    close_reason text CHECK (close_reason IS NULL OR close_reason IN ('tp', 'sl', 'manual')),
    exit_price numeric,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_trades_opened_at ON trades (opened_at DESC);
CREATE INDEX idx_trades_status ON trades (status);
CREATE INDEX idx_trades_open_ticker ON trades (ticker) WHERE status = 'open';

CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all operations on trades"
    ON trades FOR ALL USING (true) WITH CHECK (true);
