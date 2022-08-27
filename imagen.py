import os
import re
import string
import random
import logging
import subprocess
from time import sleep

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(message)s', '%H:%M'
))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Imagen:
    def __init__(
        self,
        text_prompt,
        querries_dir='querries',
        images_dir='images',
        sh_dir='sh',
        sge_out_dir='sge_out',
        python_generator_scriptname='hf_generate.py',
        time_step=30,
        timeout_steps=20,
        gpu_ram=24,
    ):
        if not os.path.exists(querries_dir):
            logging.info(f'{querries_dir} does not exist. Creating a new one...')
            os.makedirs(querries_dir)
        if not os.path.exists(images_dir):
            logging.info(f'{images_dir} does not exist. Creating a new one...')
            os.makedirs(images_dir)
        if not os.path.exists(sh_dir):
            logging.info(f'{sh_dir} does not exist. Creating a new one...')
            os.makedirs(sh_dir)
        if not os.path.exists(sge_out_dir):
            logging.info(f'{sge_out_dir} does not exist. Creating a new one...')
            os.makedirs(sge_out_dir)

        self.sge_out_dir = sge_out_dir
        self.images_dir = images_dir
        self.querries_dir = querries_dir
        self.sh_dir = sh_dir
        self.time_step = time_step
        self.timeout_step = timeout_steps
        self.gpu_ram = gpu_ram

        self.text_prompt = text_prompt

        self.python_generator_scriptname = python_generator_scriptname

        self.querry_id = self._generate_id()
        self.text_prompt_file = os.path.join(querries_dir, f'{self.querry_id}.txt')
        self.image_file = os.path.join(images_dir, f'{self.querry_id}.jpg')
        self.sh_file =None

        logger.info(f'querry_id: {self.querry_id}')
        logger.info(f'text_prompt_file: {self.text_prompt_file}')
        logger.info(f'querry_id: {self.querry_id}. -- may be unused\n')


    def generate_image(self, ):
        # we need to have a file with a text, right?
        self._create_text_prompt_file()
        logger.info(f'text prompt file {self.text_prompt_file} has been generated')
        self._generate_qsub_command()
        logger.info(f'qsub command {self.sh_file} has been created\n')

        if not self._submit_qsub_command():
            return None

        return self.image_file

    def _create_text_prompt_file(self):
        with open(self.text_prompt_file, 'w') as f:
            logger.info('im not sure about the correctness of this line...')
            newline_normalized = re.sub('\n+', '\n', self.text_prompt)
            f.write(newline_normalized)
        logger.info(f'Anyways, file {self.text_prompt_file} has been created\n')

    def _generate_qsub_command(self):
        r"""
            generate id bash script, where $0 == id
            if it is possible to play with strings in bash, we are done
        """
        self.sh_file = os.path.join(self.sh_dir, f'{self.querry_id}.sh')
        sge_out_abs = os.path.abspath(self.sge_out_dir)
        sge_out_abs = os.path.join(sge_out_abs, self.querry_id)
        cwd = os.getcwd()

        with open(self.sh_file, 'w') as f:
            f.write(
                '#!/bin/bash\n'
                '#$ -S /bin/bash\n'
                f'#$ -N stabDiff_{self.querry_id}\n'
                f'#$ -o {sge_out_abs}.out\n'
                f'#$ -e {sge_out_abs}.err\n'
                '#$ -q long.q@*\n'
                f'#$ -l matylda3=0.01,gpu=1,gpu_ram={self.gpu_ram}G,mem_free=20G,ram_free=32G,cpu=1\n'
            )

            f.write(
                '\n\n'
                f'querry_id={self.querry_id}\n'
                f'cd {cwd} || {{ exit 1 ; }}\n'
                f'source /mnt/matylda3/xskura01/miniconda3/envs/activate_text.sh || {{ exit 2 ; }}\n'
                f'python {self.python_generator_scriptname} --querry_id ${{querry_id}}\\\n'
                f'                                --querries_dir {self.querries_dir}\\\n'
                f'                                --images_dir {self.images_dir}\n\n'
            )

            logger.info('qsub command hav successefuly been generated (I\'m almost sure)\n')

    def _submit_qsub_command(self):
        cmd = subprocess.run(
            ['qsub', self.sh_file],
        )
        if cmd.returncode:
            logger.info(f'qsub command returned non-zero code')
            return False

        return True
        timeout_steps = 0
        while not os.path.exists(self.image_file) and timeout_steps < self.timeout_step:
            sleep(self.time_step)
            timeout_steps += 1
            logger.info(f'Waiting untill image is generated {self.image_file}, step: {timeout_steps}/{self.timeout_step}')
        return True


    @staticmethod
    def _generate_id(size=12, chars=None):
        if chars is None:
            chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

