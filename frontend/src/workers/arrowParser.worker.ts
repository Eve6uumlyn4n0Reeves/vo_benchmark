/*
 * Arrow Parser Module Worker (local, no CDN)
 * - Parses Arrow IPC for trajectory and PR-curve using apache-arrow dependency
 * - Message protocol compatible with existing ArrowService (id/type/data)
 */

import { tableFromIPC, Table } from 'apache-arrow';

interface ArrowWorkerMessage {
  id: string;
  type: 'parseTrajectory' | 'parsePRCurve';
  data: ArrayBuffer;
}

interface ArrowWorkerResponse {
  id: string;
  success: boolean;
  result?: any;
  error?: { message: string; stack?: string };
}

function parseTrajectoryFromTable(table: Table): any {
  const col = (name: string) => (table.getColumn(name) ? table.getColumn(name)!.toArray() : null);
  const x = col('x');
  const y = col('y');
  const z = col('z');
  const t = col('t');
  const frame = col('frame_id');

  const list = [] as Array<any>;
  if (x && y && z && t) {
    for (let i = 0; i < x.length; i++) {
      list.push({
        x: Number(x[i]),
        y: Number(y[i]),
        z: Number(z[i]),
        timestamp: Number(t[i]),
        frame_id: frame ? Number(frame[i]) : i,
      });
    }
  }

  const pack = (prefix: string) => {
    const gx = col(`${prefix}x`);
    const gy = col(`${prefix}y`);
    const gz = col(`${prefix}z`);
    const gt = col(`${prefix}t`);
    if (gx && gy && gz && gt) {
      const arr = [] as Array<any>;
      for (let i = 0; i < gx.length; i++) {
        arr.push({ x: Number(gx[i]), y: Number(gy[i]), z: Number(gz[i]), timestamp: Number(gt[i]) });
      }
      return arr;
    }
    return undefined;
  };

  // decode schema metadata into plain object<string,string>
  const meta = table.schema?.metadata ?? null;
  const metadata: Record<string, string> = {};
  if (meta) {
    // Apache Arrow JS uses Map<string,string>
    (meta as any).forEach((v: any, k: any) => {
      metadata[String(k)] = String(v);
    });
  }

  return {
    estimated_trajectory: list,
    groundtruth_trajectory: pack('gt_'),
    reference_trajectory: pack('ref_'),
    metadata,
  };
}

function parsePRCurveFromTable(table: Table): any {
  const toList = (name: string) => (table.getColumn(name) ? Array.from(table.getColumn(name)!.toArray()).map(Number) : []);
  const result: any = {
    precisions: toList('precision'),
    recalls: toList('recall'),
    thresholds: toList('threshold'),
  };
  if (table.getColumn('f1')) result.f1_scores = toList('f1');
  if (table.getColumn('raw_precision')) result.raw_precisions = toList('raw_precision');
  if (table.getColumn('raw_recall')) result.raw_recalls = toList('raw_recall');
  if (table.getColumn('raw_threshold')) result.raw_thresholds = toList('raw_threshold');
  if (table.getColumn('raw_f1')) result.raw_f1_scores = toList('raw_f1');

  const meta = table.schema?.metadata ?? null;
  const metadata: Record<string, string> = {};
  if (meta) {
    (meta as any).forEach((v: any, k: any) => {
      metadata[String(k)] = String(v);
    });
  }
  result.metadata = metadata;
  return result;
}

self.onmessage = (e: MessageEvent<ArrowWorkerMessage>) => {
  const { id, type, data } = e.data;
  const respond = (payload: ArrowWorkerResponse) => (self as any).postMessage(payload);

  try {
    const table = tableFromIPC(new Uint8Array(data));
    let result: any;
    if (type === 'parseTrajectory') result = parseTrajectoryFromTable(table as Table);
    else if (type === 'parsePRCurve') result = parsePRCurveFromTable(table as Table);
    else throw new Error(`Unknown parse type: ${type}`);

    respond({ id, success: true, result });
  } catch (err: any) {
    respond({ id, success: false, error: { message: err?.message || String(err), stack: err?.stack } });
  }
};

