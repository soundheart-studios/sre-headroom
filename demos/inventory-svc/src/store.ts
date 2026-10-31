const stock = new Map<string, number>();

export async function getStock(sku: string): Promise<number> {
  return stock.get(sku) ?? 0;
}

export async function setStock(sku: string, qty: number): Promise<void> {
  stock.set(sku, qty);
}
