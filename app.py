from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import mysql.connector
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = 'nilai_siswa_secret_key_2024'


# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────

DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': '',
    'database': 'db_nilai_siswa',
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────
#  DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])

        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM tb_user WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cur.fetchone()
        db.close()

        if user:
            session['user_id']  = user['id_user']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f'Selamat datang, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
#  DASHBOARD (per role)
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    role  = session['role']
    stats = {}

    if role == 'Admin':
        cur.execute("SELECT COUNT(*) AS total FROM tb_siswa")
        stats['total_siswa'] = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) AS total FROM tb_guru")
        stats['total_guru'] = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) AS total FROM tb_nilai")
        stats['total_nilai'] = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) AS total FROM tb_nilai WHERE status_lulus = 'Lulus'")
        stats['total_lulus'] = cur.fetchone()['total']

        db.close()
        return render_template('dashboard_admin.html', stats=stats)

    elif role == 'Guru':
        stats['total_input'] = 0
        cur.execute("SELECT * FROM tb_guru WHERE id_user = %s", (session['user_id'],))
        guru = cur.fetchone()
        if guru:
            session['id_guru'] = guru['id_guru']
            cur.execute(
                "SELECT COUNT(*) AS total FROM tb_nilai WHERE id_guru = %s",
                (guru['id_guru'],)
            )
            stats['total_input'] = cur.fetchone()['total']

        cur.execute("SELECT COUNT(*) AS total FROM tb_siswa")
        stats['total_siswa'] = cur.fetchone()['total']

        db.close()
        return render_template('guru/dashboard_guru.html', stats=stats)

    elif role == 'Siswa':
        cur.execute("SELECT * FROM tb_siswa WHERE id_user = %s", (session['user_id'],))
        siswa = cur.fetchone()
        if siswa:
            session['nis']  = siswa['nis']
            cur.execute(
                """
                SELECT n.*, mp.nama_mapel
                FROM tb_nilai n
                JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
                WHERE n.nis = %s
                ORDER BY n.created_at DESC
                """,
                (siswa['nis'],)
            )
            stats['nilai_list'] = cur.fetchall()
            stats['siswa']      = siswa
        else:
            stats['nilai_list'] = []
            stats['siswa']      = None

        db.close()
        return render_template('siswa/dashboard_siswa.html', stats=stats)

    db.close()
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
#  ADMIN: SISWA
# ─────────────────────────────────────────────

@app.route('/siswa')
@login_required
@role_required('Admin')
def list_siswa():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT s.*, u.username
        FROM tb_siswa s
        JOIN tb_user u ON s.id_user = u.id_user
        ORDER BY s.kelas, s.nama_siswa
        """
    )
    siswa_list = cur.fetchall()
    db.close()
    return render_template('siswa/list.html', siswa_list=siswa_list)


@app.route('/siswa/tambah', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def tambah_siswa():
    if request.method == 'POST':
        nis      = request.form['nis']
        nama     = request.form['nama_siswa']
        kelas    = request.form['kelas']
        username = request.form['username']
        password = hash_password(request.form['password'])

        db  = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO tb_user (username, password, role) VALUES (%s, %s, 'Siswa')",
                (username, password)
            )
            id_user = cur.lastrowid
            cur.execute(
                "INSERT INTO tb_siswa (nis, id_user, nama_siswa, kelas) VALUES (%s, %s, %s, %s)",
                (nis, id_user, nama, kelas)
            )
            db.commit()
            flash('Data siswa berhasil ditambahkan.', 'success')
            return redirect(url_for('list_siswa'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            db.close()

    return render_template('siswa/form.html', action='Tambah', data=None)


@app.route('/siswa/ubah/<nis>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def ubah_siswa(nis):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT s.*, u.username FROM tb_siswa s JOIN tb_user u ON s.id_user = u.id_user WHERE s.nis = %s",
        (nis,)
    )
    data = cur.fetchone()

    if request.method == 'POST':
        nama     = request.form['nama_siswa']
        kelas    = request.form['kelas']
        username = request.form['username']
        try:
            cur.execute("UPDATE tb_siswa SET nama_siswa = %s, kelas = %s WHERE nis = %s", (nama, kelas, nis))
            cur.execute("UPDATE tb_user SET username = %s WHERE id_user = %s", (username, data['id_user']))
            if request.form.get('password'):
                pw = hash_password(request.form['password'])
                cur.execute("UPDATE tb_user SET password = %s WHERE id_user = %s", (pw, data['id_user']))
            db.commit()
            flash('Data siswa berhasil diubah.', 'success')
            return redirect(url_for('list_siswa'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            db.close()
    else:
        db.close()

    return render_template('siswa/form.html', action='Ubah', data=data)


@app.route('/siswa/hapus/<nis>', methods=['POST'])
@login_required
@role_required('Admin')
def hapus_siswa(nis):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id_user FROM tb_siswa WHERE nis = %s", (nis,))
    siswa = cur.fetchone()
    try:
        cur.execute("DELETE FROM tb_nilai WHERE nis = %s", (nis,))
        cur.execute("DELETE FROM tb_siswa WHERE nis = %s", (nis,))
        cur.execute("DELETE FROM tb_user  WHERE id_user = %s", (siswa['id_user'],))
        db.commit()
        flash('Data siswa berhasil dihapus.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('list_siswa'))


# ─────────────────────────────────────────────
#  ADMIN: GURU
# ─────────────────────────────────────────────

@app.route('/guru')
@login_required
@role_required('Admin')
def list_guru():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        """
        SELECT g.*, u.username
        FROM tb_guru g
        JOIN tb_user u ON g.id_user = u.id_user
        ORDER BY g.nama_guru
        """
    )
    guru_list = cur.fetchall()
    db.close()
    return render_template('guru/list.html', guru_list=guru_list)


@app.route('/guru/tambah', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def tambah_guru():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tb_mata_pelajaran ORDER BY nama_mapel")
    mapel_list = cur.fetchall()

    if request.method == 'POST':
        id_guru  = request.form['id_guru']
        nama     = request.form['nama_guru']
        id_mapel = request.form.get('id_mapel', '')
        username = request.form['username']
        password = hash_password(request.form['password'])

        try:
            cur.execute(
                "INSERT INTO tb_user (username, password, role) VALUES (%s, %s, 'Guru')",
                (username, password)
            )
            id_user = cur.lastrowid
            cur.execute(
                "INSERT INTO tb_guru (id_guru, id_user, nama_guru) VALUES (%s, %s, %s)",
                (id_guru, id_user, nama)
            )
            db.commit()
            flash('Data guru berhasil ditambahkan.', 'success')
            db.close()
            return redirect(url_for('list_guru'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            db.close()

    else:
        db.close()

    return render_template('guru/form.html', action='Tambah', data=None, mapel_list=mapel_list)


@app.route('/guru/ubah/<id_guru>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def ubah_guru(id_guru):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT g.*, u.username FROM tb_guru g JOIN tb_user u ON g.id_user = u.id_user WHERE g.id_guru = %s",
        (id_guru,)
    )
    data = cur.fetchone()
    cur.execute("SELECT * FROM tb_mata_pelajaran ORDER BY nama_mapel")
    mapel_list = cur.fetchall()

    if request.method == 'POST':
        nama     = request.form['nama_guru']
        username = request.form['username']
        try:
            cur.execute("UPDATE tb_guru SET nama_guru = %s WHERE id_guru = %s", (nama, id_guru))
            cur.execute("UPDATE tb_user SET username = %s WHERE id_user = %s", (username, data['id_user']))
            if request.form.get('password'):
                pw = hash_password(request.form['password'])
                cur.execute("UPDATE tb_user SET password = %s WHERE id_user = %s", (pw, data['id_user']))
            db.commit()
            flash('Data guru berhasil diubah.', 'success')
            return redirect(url_for('list_guru'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            db.close()
    else:
        db.close()

    return render_template('guru/form.html', action='Ubah', data=data, mapel_list=mapel_list)


@app.route('/guru/hapus/<id_guru>', methods=['POST'])
@login_required
@role_required('Admin')
def hapus_guru(id_guru):
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id_user FROM tb_guru WHERE id_guru = %s", (id_guru,))
    guru = cur.fetchone()
    try:
        cur.execute("DELETE FROM tb_guru WHERE id_guru = %s", (id_guru,))
        cur.execute("DELETE FROM tb_user WHERE id_user = %s", (guru['id_user'],))
        db.commit()
        flash('Data guru berhasil dihapus.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('list_guru'))


# ─────────────────────────────────────────────
#  NILAI
# ─────────────────────────────────────────────

@app.route('/nilai')
@login_required
@role_required('Guru', 'Admin')
def list_nilai():
    db  = get_db()
    cur = db.cursor(dictionary=True)

    if session['role'] == 'Guru':
        id_guru = session.get('id_guru')
        if not id_guru:
            cur.execute("SELECT id_guru FROM tb_guru WHERE id_user = %s", (session['user_id'],))
            g = cur.fetchone()
            id_guru = g['id_guru'] if g else None
            session['id_guru'] = id_guru
        cur.execute(
            """
            SELECT n.*, s.nama_siswa, s.kelas, mp.nama_mapel
            FROM tb_nilai n
            JOIN tb_siswa s ON n.nis = s.nis
            JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
            WHERE n.id_guru = %s
            ORDER BY n.created_at DESC
            """,
            (id_guru,)
        )
    else:
        cur.execute(
            """
            SELECT n.*, s.nama_siswa, s.kelas, mp.nama_mapel, g.nama_guru
            FROM tb_nilai n
            JOIN tb_siswa s ON n.nis = s.nis
            JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
            JOIN tb_guru g ON n.id_guru = g.id_guru
            ORDER BY n.created_at DESC
            """
        )

    nilai_list = cur.fetchall()
    db.close()
    return render_template('nilai/list.html', nilai_list=nilai_list)


@app.route('/nilai/input', methods=['GET', 'POST'])
@login_required
@role_required('Guru')
def input_nilai():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tb_siswa ORDER BY kelas, nama_siswa")
    siswa_list = cur.fetchall()
    cur.execute("SELECT * FROM tb_mata_pelajaran ORDER BY nama_mapel")
    mapel_list = cur.fetchall()

    if request.method == 'POST':
        nis      = request.form['nis']
        id_mapel = request.form['id_mapel']
        tugas    = float(request.form['nilai_tugas'])
        uts      = float(request.form['nilai_uts'])
        uas      = float(request.form['nilai_uas'])

        if not all(0 <= v <= 100 for v in [tugas, uts, uas]):
            flash('Nilai harus berada pada rentang 0 hingga 100!', 'danger')
            db.close()
            return render_template('nilai/input.html', siswa_list=siswa_list, mapel_list=mapel_list)

        nilai_akhir  = (0.30 * tugas) + (0.30 * uts) + (0.40 * uas)
        status_lulus = 'Lulus' if nilai_akhir >= 70 else 'Tidak Lulus'

        cur.execute("SELECT id_guru FROM tb_guru WHERE id_user = %s", (session['user_id'],))
        guru    = cur.fetchone()
        id_guru = guru['id_guru']
        session['id_guru'] = id_guru

        try:
            cur.execute(
                "SELECT id_nilai FROM tb_nilai WHERE nis = %s AND id_mapel = %s AND id_guru = %s",
                (nis, id_mapel, id_guru)
            )
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    """
                    UPDATE tb_nilai
                    SET nilai_tugas = %s, nilai_uts = %s, nilai_uas = %s,
                        nilai_akhir = %s, status_lulus = %s
                    WHERE id_nilai = %s
                    """,
                    (tugas, uts, uas, nilai_akhir, status_lulus, existing['id_nilai'])
                )
                flash(f'Nilai berhasil diperbarui. Nilai Akhir: {nilai_akhir:.1f} — {status_lulus}', 'success')
            else:
                cur.execute(
                    """
                    INSERT INTO tb_nilai
                        (nis, id_mapel, id_guru, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, status_lulus)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (nis, id_mapel, id_guru, tugas, uts, uas, nilai_akhir, status_lulus)
                )
                flash(f'Nilai berhasil disimpan. Nilai Akhir: {nilai_akhir:.1f} — {status_lulus}', 'success')

            db.commit()
            return redirect(url_for('list_nilai'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            db.close()
    else:
        db.close()

    return render_template('nilai/input.html', siswa_list=siswa_list, mapel_list=mapel_list)


@app.route('/nilai/hapus/<int:id_nilai>', methods=['POST'])
@login_required
@role_required('Admin', 'Guru')
def hapus_nilai(id_nilai):
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM tb_nilai WHERE id_nilai = %s", (id_nilai,))
        db.commit()
        flash('Data nilai berhasil dihapus.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('list_nilai'))


# ─────────────────────────────────────────────
#  MATA PELAJARAN
# ─────────────────────────────────────────────

@app.route('/mapel')
@login_required
@role_required('Admin')
def list_mapel():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tb_mata_pelajaran ORDER BY nama_mapel")
    mapel_list = cur.fetchall()
    db.close()
    return render_template('mapel/list.html', mapel_list=mapel_list)


@app.route('/mapel/tambah', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def tambah_mapel():
    if request.method == 'POST':
        id_mapel   = request.form['id_mapel']
        nama_mapel = request.form['nama_mapel']

        db  = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "INSERT INTO tb_mata_pelajaran VALUES (%s, %s)",
                (id_mapel, nama_mapel)
            )
            db.commit()
            flash('Mata pelajaran berhasil ditambahkan.', 'success')
            return redirect(url_for('list_mapel'))
        except Exception as e:
            db.rollback()
            flash(f'Error: {e}', 'danger')
        finally:
            db.close()

    return render_template('mapel/form.html', action='Tambah', data=None)


@app.route('/mapel/hapus/<id_mapel>', methods=['POST'])
@login_required
@role_required('Admin')
def hapus_mapel(id_mapel):
    db  = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM tb_mata_pelajaran WHERE id_mapel = %s", (id_mapel,))
        db.commit()
        flash('Mata pelajaran berhasil dihapus.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        db.close()
    return redirect(url_for('list_mapel'))


# ─────────────────────────────────────────────
#  LAPORAN
# ─────────────────────────────────────────────

@app.route('/laporan')
@login_required
@role_required('Admin', 'Guru')
def laporan():
    db  = get_db()
    cur = db.cursor(dictionary=True)

    kelas_filter  = request.args.get('kelas', '')
    mapel_filter  = request.args.get('mapel', '')
    nama_filter   = request.args.get('nama', '')

    query  = """
        SELECT n.*, s.nama_siswa, s.kelas, mp.nama_mapel, g.nama_guru
        FROM tb_nilai n
        JOIN tb_siswa s ON n.nis = s.nis
        JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
        JOIN tb_guru g ON n.id_guru = g.id_guru
        WHERE 1 = 1
    """
    params = []

    if kelas_filter:
        query += " AND s.kelas = %s"
        params.append(kelas_filter)
    if mapel_filter:
        query += " AND n.id_mapel = %s"
        params.append(mapel_filter)
    if nama_filter:
        query += " AND s.nama_siswa LIKE %s"
        params.append(f'%{nama_filter}%')

    query += " ORDER BY s.kelas, s.nama_siswa"
    cur.execute(query, params)
    laporan_list = cur.fetchall()

    cur.execute("SELECT DISTINCT kelas FROM tb_siswa ORDER BY kelas")
    kelas_list = [r['kelas'] for r in cur.fetchall()]

    cur.execute("SELECT * FROM tb_mata_pelajaran ORDER BY nama_mapel")
    mapel_list = cur.fetchall()

    db.close()
    return render_template(
        'laporan.html',
        laporan_list=laporan_list,
        kelas_list=kelas_list,
        mapel_list=mapel_list,
        kelas_filter=kelas_filter,
        mapel_filter=mapel_filter,
        nama_filter=nama_filter,
    )


# ─────────────────────────────────────────────
#  EXPORT PDF (via browser print / jsPDF)
#  Route ini hanya menyediakan data untuk
#  halaman print-preview yang di-trigger JS
# ─────────────────────────────────────────────

@app.route('/export/siswa')
@login_required
@role_required('Admin')
def export_siswa():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, u.username
        FROM tb_siswa s JOIN tb_user u ON s.id_user = u.id_user
        ORDER BY s.kelas, s.nama_siswa
    """)
    data = cur.fetchall()
    db.close()
    return render_template('export/siswa_pdf.html', data=data)


@app.route('/export/guru')
@login_required
@role_required('Admin')
def export_guru():
    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT g.*, u.username
        FROM tb_guru g JOIN tb_user u ON g.id_user = u.id_user
        ORDER BY g.nama_guru
    """)
    data = cur.fetchall()
    db.close()
    return render_template('export/guru_pdf.html', data=data)


@app.route('/export/nilai')
@login_required
@role_required('Admin', 'Guru')
def export_nilai():
    db  = get_db()
    cur = db.cursor(dictionary=True)

    if session['role'] == 'Guru':
        id_guru = session.get('id_guru')
        if not id_guru:
            cur.execute("SELECT id_guru FROM tb_guru WHERE id_user = %s", (session['user_id'],))
            g = cur.fetchone()
            id_guru = g['id_guru'] if g else None
        cur.execute("""
            SELECT n.*, s.nama_siswa, s.kelas, mp.nama_mapel
            FROM tb_nilai n
            JOIN tb_siswa s ON n.nis = s.nis
            JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
            WHERE n.id_guru = %s
            ORDER BY n.created_at DESC
        """, (id_guru,))
    else:
        cur.execute("""
            SELECT n.*, s.nama_siswa, s.kelas, mp.nama_mapel, g.nama_guru
            FROM tb_nilai n
            JOIN tb_siswa s ON n.nis = s.nis
            JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
            JOIN tb_guru g ON n.id_guru = g.id_guru
            ORDER BY n.created_at DESC
        """)

    data = cur.fetchall()
    db.close()
    return render_template('export/nilai_pdf.html', data=data)


@app.route('/export/laporan')
@login_required
@role_required('Admin', 'Guru')
def export_laporan():
    db  = get_db()
    cur = db.cursor(dictionary=True)

    kelas_filter = request.args.get('kelas', '')
    mapel_filter = request.args.get('mapel', '')
    nama_filter  = request.args.get('nama', '')

    query = """
        SELECT n.*, s.nama_siswa, s.kelas, mp.nama_mapel, g.nama_guru
        FROM tb_nilai n
        JOIN tb_siswa s ON n.nis = s.nis
        JOIN tb_mata_pelajaran mp ON n.id_mapel = mp.id_mapel
        JOIN tb_guru g ON n.id_guru = g.id_guru
        WHERE 1=1
    """
    params = []
    if kelas_filter:
        query += " AND s.kelas = %s"
        params.append(kelas_filter)
    if mapel_filter:
        query += " AND n.id_mapel = %s"
        params.append(mapel_filter)
    if nama_filter:
        query += " AND s.nama_siswa LIKE %s"
        params.append(f'%{nama_filter}%')
    query += " ORDER BY s.kelas, s.nama_siswa"

    cur.execute(query, params)
    data = cur.fetchall()
    db.close()
    return render_template('export/laporan_pdf.html', data=data,
                           kelas_filter=kelas_filter, mapel_filter=mapel_filter, nama_filter=nama_filter)


# ─────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
