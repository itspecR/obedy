import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import { initLightMode } from "./composables/useLightMode";
import { router } from "./router";
import "./styles/base.css";

initLightMode();
createApp(App).use(createPinia()).use(router).mount("#app");
