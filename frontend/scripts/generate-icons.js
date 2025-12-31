/**
 * Icon Generation Script for PWA
 *
 * This script generates all required PWA icons from a source image.
 *
 * Usage:
 *   1. Place a high-resolution source image (at least 512x512) at public/icon-source.png
 *   2. Install sharp: npm install --save-dev sharp
 *   3. Run: node scripts/generate-icons.js
 *
 * This will generate all icon sizes needed for the PWA manifest and Apple devices.
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const ICON_SIZES = [72, 96, 128, 144, 152, 180, 192, 384, 512];
const SOURCE_ICON = path.join(__dirname, '../public/icon-source.png');
const PUBLIC_DIR = path.join(__dirname, '../public');

async function generateIcons() {
  console.log('🎨 Starting icon generation...\n');

  // Check if source icon exists
  if (!fs.existsSync(SOURCE_ICON)) {
    console.error('❌ Error: Source icon not found at public/icon-source.png');
    console.log('\n📝 To use this script:');
    console.log('   1. Create a high-resolution icon (at least 512x512px)');
    console.log('   2. Save it as public/icon-source.png');
    console.log('   3. Run this script again\n');
    process.exit(1);
  }

  try {
    // Get source image metadata
    const metadata = await sharp(SOURCE_ICON).metadata();
    console.log(`✅ Source icon found: ${metadata.width}x${metadata.height}`);

    if (metadata.width < 512 || metadata.height < 512) {
      console.warn('⚠️  Warning: Source icon is smaller than 512x512. Quality may be reduced.');
    }

    // Generate each icon size
    for (const size of ICON_SIZES) {
      const outputPath = path.join(PUBLIC_DIR, `icon-${size}.png`);

      await sharp(SOURCE_ICON)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 138, g: 92, b: 246, alpha: 1 } // Purple background (#8B5CF6)
        })
        .png({ quality: 100 })
        .toFile(outputPath);

      console.log(`  ✓ Generated icon-${size}.png`);
    }

    // Generate favicon
    await sharp(SOURCE_ICON)
      .resize(32, 32)
      .png()
      .toFile(path.join(PUBLIC_DIR, 'favicon.png'));
    console.log('  ✓ Generated favicon.png');

    // Generate Apple touch icon
    await sharp(SOURCE_ICON)
      .resize(180, 180)
      .png()
      .toFile(path.join(PUBLIC_DIR, 'apple-touch-icon.png'));
    console.log('  ✓ Generated apple-touch-icon.png');

    console.log('\n✨ Icon generation complete!');
    console.log('\n📋 Generated icons:');
    ICON_SIZES.forEach(size => console.log(`   - icon-${size}.png`));
    console.log('   - favicon.png');
    console.log('   - apple-touch-icon.png');
    console.log('\n🚀 Your PWA icons are ready to use!\n');

  } catch (error) {
    console.error('❌ Error generating icons:', error.message);
    process.exit(1);
  }
}

generateIcons();
