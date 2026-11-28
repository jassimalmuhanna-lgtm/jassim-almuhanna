// Entry: renders the film (vertical 1080×1920)
import { makeComp } from './gl.js';
import { BOIL } from './crayon.js';
const comp = makeComp(document.getElementById('gl'));
await Promise.all(['700 40px "Baloo Bhaijaan 2"', '800 40px "Baloo Bhaijaan 2"', '600 40px "Baloo Bhaijaan 2"'].map(f => document.fonts.load(f, 'كوخ روزا abc')));
const M = await import('./film.js');
window.DUR = M.DUR; window.EV = M.EV; window.TEXTS = M.TEXTS;
window.render = t => { BOIL.step = Math.floor(t * 12 + 1e-6); M.frame(comp, t); };
window.READY = true;
