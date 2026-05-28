'use client';
import RA_EXPERIMENTS from '@/components/Fab/constants/raExperiments';
import TM_EXPERIMENTS from '@/components/Fab/constants/tmExperiments';

const ALL_EXPERIMENTS = [
  ...RA_EXPERIMENTS.map((e) => ({ ...e, group: 'RA' })),
  ...TM_EXPERIMENTS.map((e) => ({ ...e, group: 'TM' })),
];
export default ALL_EXPERIMENTS;
export { ALL_EXPERIMENTS };
