"use client";
import EXPERIMENTS from '@/components/Lab/constants/experiments';

const findExp=id=>EXPERIMENTS.find(e=>e.id===id);
export default findExp;
export { findExp };
