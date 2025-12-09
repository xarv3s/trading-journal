
export interface ChartData {
    time: number; // Unix timestamp
    value: number;
}

export function calculateEMA(data: ChartData[], period: number): ChartData[] {
    const k = 2 / (period + 1);
    const emaData: ChartData[] = [];

    let ema = data[0].value; // Start with SMA (or just first value for simplicity)

    // Simple initialization: use first value as initial EMA
    // A more accurate way is to calculate SMA for first 'period' elements, but for long series this converges quickly.

    for (const point of data) {
        ema = point.value * k + ema * (1 - k);
        emaData.push({
            time: point.time,
            value: ema
        });
    }

    return emaData;
}
