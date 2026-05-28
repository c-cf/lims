'use client';
import EXPERIMENTS from '@/components/Lab/constants/experiments';

const findExp = (id: string | number | null | undefined) => EXPERIMENTS.find((e) => e.id === id);
export default findExp;
export { findExp };
