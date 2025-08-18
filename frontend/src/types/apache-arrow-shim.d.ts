declare module 'apache-arrow' {
  // Minimal typings sufficient for our worker usage
  export type Table = any;
  export function tableFromIPC(data: Uint8Array | ArrayBufferView | Iterable<number>): Table;
}

