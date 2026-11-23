const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const yml = fs.readFileSync(
  path.join(__dirname, "../.github/workflows/deploy-pages.yml"),
  "utf8"
);

test("Pages upload finishes in an earlier job than deploy", () => {
  assert.match(yml, /^ {2}build:/m);
  assert.match(yml, /^ {2}deploy:/m);
  assert.match(yml, /needs:\s*build/);
  const build = yml.slice(yml.indexOf("build:"), yml.indexOf("deploy:"));
  const deploy = yml.slice(yml.indexOf("deploy:"));
  assert.match(build, /actions\/upload-pages-artifact@v3/);
  assert.doesNotMatch(build, /actions\/deploy-pages@/);
  assert.match(deploy, /actions\/deploy-pages@v4/);
  assert.doesNotMatch(deploy, /actions\/upload-pages-artifact@/);
  assert.match(yml, /cancel-in-progress:\s*false/);
});
