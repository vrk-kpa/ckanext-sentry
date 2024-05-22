const environment = document.querySelector("[data-sentry]").getAttribute('data-environment')
const tracesSampleRate = document.querySelector("[data-sentry]").getAttribute('data-tracesSampleRate')

Sentry.init({
    release: "",
    tracesSampleRate: tracesSampleRate,
    environment: environment
});

