let dsn = document.querySelector("[data-sentry]").getAttribute('data-dsn')
let environment = document.querySelector("[data-sentry]").getAttribute('data-environment')
Sentry.init({
    dsn: dsn,
    release: "",
    integrations: [],
    tracesSampleRate: 0.2,
    environment: environment
});

