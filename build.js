const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('==> Starting deployment build for Vercel...');

// Ensure NITRO_PRESET=vercel so Nitro produces Vercel Build Output API v3
process.env.NITRO_PRESET = process.env.NITRO_PRESET || 'vercel';
process.env.DANGEROUSLY_DEPLOY_VULNERABLE_TANSTACK_START_XSS = '1';

// Build the dashboard workspace
execSync('npm run build --workspace=dashboard', {
  stdio: 'inherit',
  env: process.env,
});

// Copy output to root .vercel/output if generated inside dashboard/.vercel/output
const dashboardVercelOutput = path.join(__dirname, 'dashboard', '.vercel', 'output');
const rootVercelOutput = path.join(__dirname, '.vercel', 'output');

if (fs.existsSync(dashboardVercelOutput)) {
  console.log('==> Assembling .vercel/output at repository root...');
  fs.mkdirSync(rootVercelOutput, { recursive: true });
  fs.cpSync(dashboardVercelOutput, rootVercelOutput, { recursive: true });
  console.log('==> Vercel Build Output API v3 successfully prepared at .vercel/output!');
}
