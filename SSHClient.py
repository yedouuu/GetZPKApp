import asyncssh
import asyncio

class SSH_Client:
    def __init__(self, host, port, username, key_path=None, password=None):
        self.host = host
        self.port = int(port)
        self.username = username
        self.key_path = key_path
        self.password = password
        self.conn = None

    async def connect(self):
        if self.key_path:
            self.conn = await asyncssh.connect(self.host, port=self.port, username=self.username, client_keys=[self.key_path])
        else:
            self.conn = await asyncssh.connect(self.host, port=self.port, username=self.username, password=self.password)
    
    async def get_sftp(self):
        return await self.conn.start_sftp_client()
    
    async def run_command(self, command):
        print("【DEBUG】Running command: " + command)
        result = await self.conn.run(command, check=True)
        return result.stdout.strip()

    async def run_command_with_progress(self, command, total, progress_callback):
        """执行命令并提供实时输出到回调函数，以更新进度条。"""
        async with self.conn.create_process(command, term_type='xterm') as process:
            stderr_data = ''
            stdout_lines = []

            async def collect_stderr():
                nonlocal stderr_data
                try:
                    async for chunk in process.stderr:
                        stderr_data += chunk
                except Exception:
                    pass

            stderr_task = asyncio.ensure_future(collect_stderr())

            try:
                buffered_updates = 0
                last_update_time = asyncio.get_event_loop().time()
                data_buffer = ''
                async for data_chunk in process.stdout:
                    data_buffer += data_chunk
                    while '\n' in data_buffer:
                        line, data_buffer = data_buffer.split('\n', 1)
                        stripped = line.strip()
                        if stripped:
                            buffered_updates += 1
                            stdout_lines.append(stripped)

                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_update_time >= 0.5:
                        progress_callback(buffered_updates, total)
                        buffered_updates = 0
                        last_update_time = current_time

                progress_callback(buffered_updates, total)
            finally:
                stderr_task.cancel()
                try:
                    await stderr_task
                except asyncio.CancelledError:
                    pass

            if process.exit_status != 0:
                error_msg = f"Command failed with exit status {process.exit_status}"
                if stderr_data.strip():
                    error_msg += f"\nStderr: {stderr_data.strip()}"
                if stdout_lines:
                    tail = stdout_lines[-20:]
                    error_msg += f"\nStdout (last {len(tail)} lines):\n" + "\n".join(tail)
                raise Exception(error_msg)
    
    async def upload_file(self, local_path, remote_path):
        await self.conn.put(local_path, remote_path)

    async def download_file(self, remote_path, local_path, progress_callback=None):
        """下载文件，支持进度回调。
        
        :param remote_path: 远程文件路径
        :param local_path: 本地文件路径
        :param progress_callback: 进度更新回调函数
        """
        await self.conn.get(remote_path, local_path, progress=progress_callback)

    async def close(self):
        self.conn.close()

# 使用示例
async def main():
    ssh = SSH_Client('your_host', 'your_username', 'your_password')
    await ssh.connect()
    output = await ssh.run_command('ls -l')  # 替换成你想要执行的命令
    print(output)
    await ssh.close()

if __name__ == "__main__":
    asyncio.run(main())
