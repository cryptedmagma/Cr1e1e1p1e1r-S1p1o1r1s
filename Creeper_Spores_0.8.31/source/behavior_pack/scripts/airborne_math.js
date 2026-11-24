// Pure, deterministic geometry used by the airborne carrier. No Bedrock API imports.
export const vecLen = v => Math.hypot(v.x, v.y, v.z);
export function normalized(v) {
  const d = vecLen(v); return d > 0.0001 ? { x:v.x/d,y:v.y/d,z:v.z/d } : { x:1,y:0,z:0 };
}
export function driftDirection(worldTick, seed) {
  // This is SIMULATED air circulation: Minecraft does not expose a wind velocity field.
  const a=(worldTick/1800+seed*1.618)*Math.PI*2;
  return normalized({x:Math.cos(a),y:Math.sin(a*.7)*.1,z:Math.sin(a)});
}
export function advanceAir(pos, dir, n=0.8) {
  return {x:pos.x+dir.x*n,y:pos.y+dir.y*n,z:pos.z+dir.z*n};
}
export function horizontalTravel(a,b) { return Math.hypot(a.x-b.x,a.z-b.z); }
