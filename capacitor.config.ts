import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.catchme.climbing',
  appName: 'CatchMe',
  webDir: 'frontend/dist',
  server: {
    androidScheme: 'https',
  },
}
export default config
