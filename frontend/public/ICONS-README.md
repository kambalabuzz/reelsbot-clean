# PWA Icons Setup Guide

This directory contains the icons needed for your Progressive Web App (PWA).

## Quick Setup

### Option 1: Generate Icons (Recommended)

1. **Create or obtain a source icon:**
   - Create a high-resolution square icon (minimum 512x512px, recommended 1024x1024px)
   - Save it as `public/icon-source.png`
   - Make sure it's a PNG file with transparency if needed

2. **Install dependencies:**
   ```bash
   npm install --save-dev sharp
   ```

3. **Generate all icon sizes:**
   ```bash
   node scripts/generate-icons.js
   ```

This will automatically create all required icon sizes:
- icon-72.png, icon-96.png, icon-128.png, icon-144.png
- icon-152.png, icon-180.png, icon-192.png, icon-384.png, icon-512.png
- favicon.png (32x32)
- apple-touch-icon.png (180x180)

### Option 2: Manual Creation

If you prefer to create icons manually, you'll need these sizes:

**PWA Manifest Icons:**
- 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

**Additional Icons:**
- favicon.png (32x32)
- apple-touch-icon.png (180x180)

**Screenshots (optional, for PWA installation prompts):**
- screenshot-wide.png (1920x1080) - Desktop view
- screenshot-narrow.png (1080x1920) - Mobile view

## Icon Design Tips

1. **Keep it simple:** Icons should be recognizable at small sizes
2. **High contrast:** Use colors that stand out
3. **Square format:** All icons should be square (1:1 aspect ratio)
4. **Safe zone:** Keep important content within the center 80% of the icon
5. **Test at multiple sizes:** Verify your icon looks good at both 72px and 512px

## Current Theme

The app uses a purple theme (#8B5CF6). Consider incorporating this color into your icon design for brand consistency.

## Verifying Icons

After generation, you can verify your PWA setup:

1. **Development:** Run `npm run dev` and check the browser console for PWA warnings
2. **Production:** Run `npm run build && npm start` and test "Add to Home Screen" on mobile
3. **Lighthouse:** Run a Lighthouse audit in Chrome DevTools to check PWA score

## Troubleshooting

**Icons not showing:**
- Clear browser cache and hard reload (Cmd/Ctrl + Shift + R)
- Check browser console for 404 errors
- Verify all icon files exist in the `public` directory

**"Add to Home Screen" not working:**
- Ensure you're using HTTPS (required for PWA)
- Check that manifest.json is correctly linked in layout.tsx
- Verify service worker is registered (check Application tab in DevTools)

## Resources

- [Web.dev PWA Icon Guide](https://web.dev/add-manifest/)
- [PWA Asset Generator](https://github.com/onderceylan/pwa-asset-generator)
- [Favicon Generator](https://realfavicongenerator.net/)
