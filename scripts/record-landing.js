const puppeteer = require('puppeteer-core');
const { PuppeteerScreenRecorder } = require('puppeteer-screen-recorder');

(async () => {
  const browser = await puppeteer.connect({
    browserURL: 'http://127.0.0.1:18800'
  });

  const pages = await browser.pages();
  let page = pages.find(p => p.url().includes('agentwallet.fun'));
  if (!page) {
    page = await browser.newPage();
  }
  
  await page.setViewport({ width: 1280, height: 720 });
  
  const recorder = new PuppeteerScreenRecorder(page, {
    fps: 30,
    videoFrame: { width: 1280, height: 720 }
  });

  const outputPath = 'C:\\Users\\black\\Desktop\\agentwallet\\landing-page\\demo.mp4';
  
  await recorder.start(outputPath);
  
  // Navigate to page (triggers boot animation)
  await page.goto('https://agentwallet.fun', { waitUntil: 'domcontentloaded' });
  
  // Wait for boot animation
  await new Promise(r => setTimeout(r, 8000));
  
  // Scroll through sections slowly
  await page.evaluate(() => window.scrollBy(0, 400));
  await new Promise(r => setTimeout(r, 2000));
  
  await page.evaluate(() => window.scrollBy(0, 400));
  await new Promise(r => setTimeout(r, 2000));
  
  await page.evaluate(() => window.scrollBy(0, 400));
  await new Promise(r => setTimeout(r, 2000));
  
  await page.evaluate(() => window.scrollBy(0, 400));
  await new Promise(r => setTimeout(r, 2000));
  
  await page.evaluate(() => window.scrollBy(0, 400));
  await new Promise(r => setTimeout(r, 2000));
  
  await page.evaluate(() => window.scrollBy(0, 400));
  await new Promise(r => setTimeout(r, 2000));

  await recorder.stop();
  
  console.log('Recording saved to:', outputPath);
  await browser.disconnect();
})();
