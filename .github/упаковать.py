# Архив проекта для «Загрузить проект из файла»: в корне Проект.yaml и подсистема.
# Имена файлов — UTF-8 с флагом UTF-8 у каждой записи; zip из Info-ZIP ставит его
# только при UTF-8-локали, иначе распаковщик читает кириллицу как CP437.
# Запуск: python3 .github/упаковать.py <папка проекта> <архив>
import sys
import zipfile
from pathlib import Path

UTF8 = 0x800

папка, архив = Path(sys.argv[1]), Path(sys.argv[2])
архив.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(архив, 'w', zipfile.ZIP_DEFLATED) as zf:
    for путь in sorted(папка.rglob('*')):
        zf.write(путь, путь.relative_to(папка).as_posix())

with zipfile.ZipFile(архив) as zf:
    записи = zf.infolist()
    без_флага = [з.filename for з in записи if not з.filename.isascii() and not з.flag_bits & UTF8]
if без_флага:
    sys.exit('Записи без флага UTF-8:\n  ' + '\n  '.join(без_флага))
print(len(записи))
