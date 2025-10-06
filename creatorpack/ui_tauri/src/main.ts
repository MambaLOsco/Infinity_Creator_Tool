const form = document.querySelector('form');
const logContainer = document.querySelector('#log');

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(form as HTMLFormElement);
  const input = formData.get('input') as string;
  const brand = formData.get('brand') as string;
  const minutes = formData.get('minutes') as string;

  const process = new (window as any).TauriShell.Command('creatorpack', ['run', '--file', input, '--minutes', minutes, ...(brand ? ['--brand', brand] : [])]);

  process.stdout.on('data', (line: string) => {
    const pre = document.createElement('pre');
    pre.textContent = line;
    logContainer?.appendChild(pre);
  });

  await process.spawn();
});
