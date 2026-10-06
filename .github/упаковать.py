# Сборка библиотеки .xlib — так её выгружает панель управления («Выгрузить сборку»):
# в корне манифест Assembly.yaml, файлы проекта — под <Поставщик>/<Имя>/, записей
# каталогов нет, у каждого имени флаг UTF-8. Без манифеста панель управления
# не принимает архив: «Кодировка имен элементов проекта Cp866 отличается от ожидаемой Utf8».
# Запуск: python3 .github/упаковать.py <папка проекта> <сборка> [коммит]
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

UTF8 = 0x800
MSDOS = 0

папка, сборка = Path(sys.argv[1]), Path(sys.argv[2])
коммит = sys.argv[3] if len(sys.argv) > 3 else ''

проект = (папка / 'Проект.yaml').read_text(encoding='utf-8')


def ключ(имя):
    найдено = re.search(rf'^{имя}: (.+)$', проект, re.M)
    if not найдено:
        sys.exit(f'В Проект.yaml нет {имя}')
    return найдено.group(1).strip()


вид = {'Библиотека': 'Library'}[ключ('ВидПроекта')]
поставщик, имя, версия = ключ('Поставщик'), ключ('Имя'), ключ('Версия')
создана = datetime.now(timezone.utc).strftime('%Y.%m.%d %H:%M:%S')
манифест = (
    'ManifestVersion: 1.0\n'
    f'ProjectKind: {вид}\n'
    f'Vendor: {поставщик}\n'
    f'Name: {имя}\n'
    f'Version: {версия}\n'
    f'Created: {создана}\n'
    f'CommitId: {коммит}\n'
    'Release:\n'
    f'    Created: {создана}\n'
)


def запись(путь_в_архиве):
    з = zipfile.ZipInfo(путь_в_архиве, datetime.now().timetuple()[:6])
    з.compress_type = zipfile.ZIP_DEFLATED
    з.create_system = MSDOS
    з.flag_bits |= UTF8
    return з


сборка.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(сборка, 'w') as zf:
    for путь in sorted(п for п in папка.rglob('*') if п.is_file()):
        zf.writestr(запись(f'{поставщик}/{имя}/{путь.relative_to(папка).as_posix()}'), путь.read_bytes())
    zf.writestr(запись('Assembly.yaml'), манифест.encode('utf-8'))



# zipfile снимает флаг UTF-8 с имён латиницей, а в выгрузке панели управления он у всех
# записей: бит ставится в локальных заголовках и в центральном каталоге прямо в байтах
def флаг_всем(байты):
    def число(с, длина):
        return int.from_bytes(байты[с:с + длина], 'little')

    def поставить(с):
        байты[с:с + 2] = (число(с, 2) | UTF8).to_bytes(2, 'little')

    with zipfile.ZipFile(сборка) as zf:
        for з in zf.infolist():
            поставить(з.header_offset + 6)
    конец = байты.rfind(b'PK\x05\x06')
    с = число(конец + 16, 4)
    for _ in range(число(конец + 10, 2)):
        поставить(с + 8)
        с += 46 + число(с + 28, 2) + число(с + 30, 2) + число(с + 32, 2)


байты = bytearray(сборка.read_bytes())
флаг_всем(байты)
сборка.write_bytes(байты)

with zipfile.ZipFile(сборка) as zf:
    if zf.testzip() is not None:
        sys.exit('Сборка повреждена')
    записи = zf.infolist()
    без_флага = [з.filename for з in записи if not з.flag_bits & UTF8]
if без_флага:
    sys.exit('Записи без флага UTF-8:\n  ' + '\n  '.join(без_флага))
print(len(записи))
