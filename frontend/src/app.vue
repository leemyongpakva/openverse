<script setup lang="ts">
import {
  computed,
  onMounted,
  useHead,
  useLocaleHead,
  useRuntimeConfig,
} from "#imports"

import { meta as commonMeta } from "#shared/constants/meta"
import { favicons } from "#shared/constants/favicons"
import { useUiStore } from "~/stores/ui"
import { useFeatureFlagStore } from "~/stores/feature-flag"
import { useLayout } from "~/composables/use-layout"
import { useDarkMode } from "~/composables/use-dark-mode"

import VSkipToContentButton from "~/components/VSkipToContentButton.vue"

const { updateBreakpoint } = useLayout()

const config = useRuntimeConfig()

const featureFlagStore = useFeatureFlagStore()
const uiStore = useUiStore()

const darkMode = useDarkMode()

/* UI store */
const isDesktopLayout = computed(() => uiStore.isDesktopLayout)
const breakpoint = computed(() => uiStore.breakpoint)
const headerHeight = computed(() => {
  return `--header-height: ${uiStore.headerHeight}px`
})

const head = useLocaleHead({ dir: true, key: "id", seo: true })

useHead({
  bodyAttrs: { class: darkMode.cssClass },
  title: "Openly Licensed Images, Audio and More | Openverse",
  meta: commonMeta,
  link: [
    ...favicons,
    {
      rel: "search",
      type: "application/opensearchdescription+xml",
      title: "Openverse",
      href: "/opensearch.xml",
    },
    {
      rel: "dns-prefetch",
      href: config.public.apiUrl,
    },
    {
      rel: "preconnect",
      href: config.public.apiUrl,
      crossorigin: "",
    },
  ],
})

/**
 * Update the breakpoint value in the cookie on mounted.
 * The Pinia state might become different from the cookie state if, for example, the cookies were saved when the screen was `sm`,
 * and then a page is opened on SSR on a `lg` screen.
 */
onMounted(() => {
  updateBreakpoint()
  featureFlagStore.syncAnalyticsWithLocalStorage()
})
</script>

<template>
  <div>
    <Html :lang="head.htmlAttrs?.lang" :dir="head.htmlAttrs?.dir">
      <Head>
        <template v-for="link in head.link" :key="link.id">
          <Link
            :id="link.id"
            :rel="link.rel"
            :href="link.href"
            :hreflang="link.hreflang"
          />
        </template>
        <template v-for="meta in head.meta" :key="meta.id">
          <Meta
            :id="meta.id"
            :property="meta.property"
            :content="meta.content"
          />
        </template>
      </Head>
      <Body :style="headerHeight">
        <div :class="[isDesktopLayout ? 'desktop' : 'mobile', breakpoint]">
          <VSkipToContentButton />
          <NuxtLayout>
            <NuxtPage />
          </NuxtLayout>
          <VGlobalAudioSection />
        </div>
      </Body>
    </Html>
  </div>
</template>
