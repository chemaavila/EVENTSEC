export function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

export function buildPath(src: [number, number], dst: [number, number], steps = 24): [number, number][] {
  const [slon, slat] = src;
  const [dlon, dlat] = dst;
  const pts: [number, number][] = [];
  for (let i = 0; i <= steps; i += 1) {
    const t = i / steps;
    const lon = lerp(slon, dlon, t);
    const latBase = lerp(slat, dlat, t);
    const bulge = Math.sin(Math.PI * t) * 8;
    const lat = latBase + bulge;
    pts.push([lon, lat]);
  }
  return pts;
}

