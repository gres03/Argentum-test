import Jimp from 'jimp';
import fs from 'fs';
import path from 'path';

const dir = './images/partners';
const files = fs.readdirSync(dir).filter(f => /\.(jpg|jpeg|png)$/i.test(f));

// How many pixels of padding to leave around the trimmed logo
const PADDING = 8;

for (const file of files) {
  const fp = path.join(dir, file);
  try {
    const img = await Jimp.read(fp);
    // autocrop removes borders of similar color (default: white/near-white)
    img.autocrop({ tolerance: 0.05, cropSymmetric: true });
    // add a little breathing room
    const w = img.getWidth() + PADDING * 2;
    const h = img.getHeight() + PADDING * 2;
    const padded = new Jimp(w, h, 0xffffffff); // white background
    padded.composite(img, PADDING, PADDING);
    await padded.writeAsync(fp);
    console.log(`✓ ${file} → ${w}x${h}`);
  } catch (e) {
    console.log(`✗ ${file}: ${e.message}`);
  }
}
console.log('Done.');
