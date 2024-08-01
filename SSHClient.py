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
            buffered_updates = 0
            last_update_time = asyncio.get_event_loop().time()
            data_buffer = ''
            async for data_chunk in process.stdout:
                # print(data_chunk)
                data_buffer += data_chunk
                while '\n' in data_buffer:
                    line, data_buffer = data_buffer.split('\n', 1)
                    if line.strip():  # 如果处理的行有效
                        buffered_updates += 1
                        #print(line.strip())  # 这里可以替换成你想要处理的输出

                # 用时间控制刷新频率，例如每0.5秒刷新一次
                current_time = asyncio.get_event_loop().time()
                if current_time - last_update_time >= 0.5:
                    progress_callback(buffered_updates, total)
                    # print(f"Processed {buffered_updates} lines so far")
                    buffered_updates = 0
                    last_update_time = current_time

            # 确保退出前最后一次更新
            progress_callback(buffered_updates, total)

            if process.exit_status != 0:
                raise Exception(f"Command failed with exit status {process.exit_status}")
    
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
