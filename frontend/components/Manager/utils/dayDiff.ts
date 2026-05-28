'use client';

const dayDiff = (a: string, b: string) => Math.round((+new Date(b) - +new Date(a)) / 86400000);
export default dayDiff;
export { dayDiff };
