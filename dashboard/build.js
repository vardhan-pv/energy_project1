import { execSync } from 'node:child_process';

console.log('==> Starting dashboard deployment build for Vercel...');

// Ensure NITRO_PRESET=vercel so Nitro produces Vercel Build Output API v3
process.env.NITRO_PRESET = process.env.NITRO_PRESET || 'vercel';
process.env.DANGEROUSLY_DEPLOY_VULNERABLE_TANSTACK_START_XSS = '1';

// Build dashboard with Vite + Nitro
execSync('npm run build', {
  stdio: 'inherit',
  env: process.env,
});

console.log('==> Vercel Build Output API v3 successfully prepared in dashboard/.vercel/output!');
