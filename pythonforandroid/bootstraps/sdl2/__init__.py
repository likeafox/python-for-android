from pythonforandroid.toolchain import Bootstrap, shprint, current_directory, info, warning, ArchAndroid, logger, info_main, which
from os.path import join, exists
from os import walk
import glob
import sh
from tempfile import mkdtemp
from shutil import rmtree

class SDL2Bootstrap(Bootstrap):
    name = 'sdl2'

    recipe_depends = ['sdl2']

    def run_distribute(self):
        info_main('# Creating Android project from build and {} bootstrap'.format(
            self.name))

        info('This currently just copies the SDL2 build stuff straight from the build dir.')
        shprint(sh.rm, '-rf', self.dist_dir)
        shprint(sh.cp, '-r', self.build_dir, self.dist_dir)
        with current_directory(self.dist_dir):
            with open('local.properties', 'w') as fileh:
                fileh.write('sdk.dir={}'.format(self.ctx.sdk_dir))

        with current_directory(self.dist_dir):
            info('Copying python distribution')

            if not exists('private'):
                shprint(sh.mkdir, 'private')
            if not exists('assets'):
                shprint(sh.mkdir, 'assets')
            
            hostpython = sh.Command(self.ctx.hostpython)
            # AND: This *doesn't* need to be in arm env?
            shprint(hostpython, '-OO', '-m', 'compileall',
                    self.ctx.get_python_install_dir())
            if not exists('python-install'):
                shprint(sh.cp, '-a', self.ctx.get_python_install_dir(), './python-install')

            info('Unpacking aars')
            for aar in glob.glob(join(self.ctx.aars_dir, '*.aar')):
                temp_dir = mkdtemp()
                name = splitext(basename(aar))[0]
                jar_name = name + '.jar'
                info("unpack {} jar".format(name))
                info("  from {}".format(aar))
                info("  to {}".format(temp_dir))
                shprint(sh.unzip, '-o', aar, '-d', temp_dir)

                jar_src = join(temp_dir, 'classes.jar')
                jar_tgt = join('libs', jar_name)
                info("cp {} jar".format(name))
                info("  from {}".format(jar_src))
                info("  to {}".format(jar_tgt))
                shprint(sh.cp, '-a',jar_src, jar_tgt)

                so_src_dir = join(temp_dir, 'jni', 'armeabi')
                so_tgt_dir = join('libs', 'armeabi')
                info("cp {} .so".format(name))
                info("  from {}".format(so_src_dir))
                info("  to {}".format(so_tgt_dir))
                shprint(sh.mkdir, '-p', so_tgt_dir)
                so_files = glob.glob(join(so_src_dir, '*.so'))
                for f in so_files:
                    shprint(sh.cp, '-a', f, so_tgt_dir)

                rmtree(temp_dir)

            info('Copying libs')
            # AND: Hardcoding armeabi - naughty!
            shprint(sh.mkdir, '-p', join('libs', 'armeabi'))
            for lib in glob.glob(join(self.ctx.get_libs_dir('armeabi'), '*')):
                shprint(sh.cp, '-a', lib, join('libs', 'armeabi'))

            info('Copying java files')
            for filename in glob.glob(self.ctx.javaclass_dir):
                shprint(sh.cp, '-a', filename, 'src')

            info('Filling private directory')
            if not exists(join('private', 'lib')):
                info('private/lib does not exist, making')
                shprint(sh.cp, '-a', join('python-install', 'lib'), 'private')
            shprint(sh.mkdir, '-p', join('private', 'include', 'python2.7'))
            
            # AND: Copylibs stuff should go here
            if exists(join('libs', 'armeabi', 'libpymodules.so')):
                shprint(sh.mv, join('libs', 'armeabi', 'libpymodules.so'), 'private/')
            shprint(sh.cp, join('python-install', 'include' , 'python2.7', 'pyconfig.h'), join('private', 'include', 'python2.7/'))

            info('Removing some unwanted files')
            shprint(sh.rm, '-f', join('private', 'lib', 'libpython2.7.so'))
            shprint(sh.rm, '-rf', join('private', 'lib', 'pkgconfig'))

            with current_directory(join(self.dist_dir, 'private', 'lib', 'python2.7')):
                # shprint(sh.xargs, 'rm', sh.grep('-E', '*\.(py|pyx|so\.o|so\.a|so\.libs)$', sh.find('.')))
                removes = []
                for dirname, something, filens in walk('.'):
                    for filename in filens:
                        for suffix in ('py', 'pyc', 'so.o', 'so.a', 'so.libs'):
                            if filename.endswith(suffix):
                                removes.append(filename)
                shprint(sh.rm, '-f', *removes)

                info('Deleting some other stuff not used on android')
                # To quote the original distribute.sh, 'well...'
                # shprint(sh.rm, '-rf', 'ctypes')
                shprint(sh.rm, '-rf', 'lib2to3')
                shprint(sh.rm, '-rf', 'idlelib')
                for filename in glob.glob('config/libpython*.a'):
                    shprint(sh.rm, '-f', filename)
                shprint(sh.rm, '-rf', 'config/python.o')
                # shprint(sh.rm, '-rf', 'lib-dynload/_ctypes_test.so')
                # shprint(sh.rm, '-rf', 'lib-dynload/_testcapi.so')


        info('Stripping libraries')
        env = ArchAndroid(self.ctx).get_env()
        strip = which('arm-linux-androideabi-strip', env['PATH'])
        if strip is None:
            warning('Can\'t find strip in PATH...')
        strip = sh.Command(strip)
        filens = shprint(sh.find, join(self.dist_dir, 'private'), join(self.dist_dir, 'libs'),
                '-iname', '*.so', _env=env).stdout.decode('utf-8')
        logger.info('Stripping libraries in private dir')
        for filen in filens.split('\n'):
            try:
                strip(filen, _env=env)
            except sh.ErrorReturnCode_1:
                logger.debug('Failed to strip ' + 'filen')
        super(SDL2Bootstrap, self).run_distribute()

bootstrap = SDL2Bootstrap()
