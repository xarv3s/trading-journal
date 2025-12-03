export interface UnifiedTrade {
    id: string;
    original_id: number;
    source_table: 'OPEN' | 'CLOSED';
    trading_symbol: string;
    instrument_token: number;
    exchange: string;
    segment: string;
    order_type: string;
    entry_date: string;
    exit_date?: string;
    qty: number;
    entry_price: number;
    exit_price?: number;
    pnl: number;
    status: string;
    is_mtf?: number;
    setup_used?: string;
    mistakes_made?: string;
    notes?: string;
    screenshot_path?: string;
    type: string;
    strategy_type?: string;
    is_basket?: number;
    ltp?: number;
    stop_loss?: number;
    open_risk?: number;
}

export interface PaginatedTradesResponse {
    data: UnifiedTrade[];
    total: number;
    page: number;
    page_size: number;
}

export interface TradeUpdate {
    notes?: string;
    mistakes_made?: string;
    setup_used?: string;
    strategy_type?: string;
    screenshot_path?: string;
    stop_loss?: number;
}
