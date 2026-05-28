'use client';

const addDays = (s: string, n: number) => {
  const d = new Date(s);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
};
export default addDays;
export { addDays };
