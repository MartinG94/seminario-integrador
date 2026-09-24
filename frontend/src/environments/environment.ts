// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json`.

export const environment = {
  production: false,
  // Ruta relativa: `ng serve` la redirige al backend con proxy.conf.json, de
  // modo que el navegador ve un único origen y no hace falta CORS.
  apiUrl: '/api/v1'
};
