"""Load a Bedrock geo + texture into Blockbench and capture renders via the MCP plugin."""
import sys, json, base64, bb

def load(geo_path, tex_path):
    geo = open(geo_path, encoding='utf-8').read()
    tex = base64.b64encode(open(tex_path, 'rb').read()).decode().replace('/', '_')
    code = """
(() => {
  if (Project) { Project.saved = true; Project.close(true); }
  newProject(Formats.bedrock);
  Codecs.bedrock.parse(%s, 'preview.geo.json');
  const t = new Texture({name: 'skin'}).fromDataURL('data:image/png;base64,' + '%s'.replace(/_/g, '/')).add(false);
  Cube.all.forEach(c => c.applyTexture(t, true));
  Canvas.updateAll();
  return {cubes: Cube.all.length, groups: Group.all.length};
})()
""" % (geo.replace("//", "/ /"), tex)
    return bb.js(code)

def shoot(out, angles=(('front_left',),)):
    pass

if __name__ == '__main__':
    print(load(sys.argv[1], sys.argv[2]))
