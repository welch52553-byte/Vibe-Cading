/**
 * OpenSCAD WASM compilation worker.
 * Loaded by index.html via: new Worker('/viewer/worker.js', { type: 'module' })
 *
 * openscad.js uses import.meta.url to locate sibling files, so importing it
 * from /wasm/openscad.js makes it correctly resolve /wasm/openscad.wasm.js
 * and /wasm/openscad.wasm without any extra configuration.
 */
import OpenSCAD from '/wasm/openscad.js';

let instance = null;

OpenSCAD({ noInitialRun: true })
  .then(m => {
    instance = m;
    self.postMessage({ type: 'ready' });
  })
  .catch(e => self.postMessage({ type: 'init_error', message: String(e) }));

self.onmessage = async ({ data }) => {
  if (data.type !== 'compile') return;

  if (!instance) {
    self.postMessage({ type: 'error', message: 'OpenSCAD 未就绪，请等待初始化完成' });
    return;
  }

  try {
    // Clean virtual FS from previous run
    try { instance.FS.unlink('/input.scad'); } catch {}
    try { instance.FS.unlink('/output.stl'); } catch {}

    instance.FS.writeFile('/input.scad', data.source);

    const args = ['/input.scad', '--enable=manifold', '-o', '/output.stl'];
    if (data.fn) args.push('-D', `$fn=${data.fn}`);

    const exitCode = instance.callMain(args);

    if (exitCode !== 0) {
      self.postMessage({ type: 'error', message: `编译退出码 ${exitCode}` });
      return;
    }

    const stl = instance.FS.readFile('/output.stl');
    self.postMessage({ type: 'result', stl: stl.buffer }, [stl.buffer]);
  } catch (e) {
    self.postMessage({ type: 'error', message: String(e) });
  }
};
