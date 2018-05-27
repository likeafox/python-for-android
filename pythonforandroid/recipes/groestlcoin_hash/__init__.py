from pythonforandroid.recipe import CythonRecipe
import os


class groestlcoin_hashRecipe(CythonRecipe):
    version = '1.0.1'
    url = 'https://pypi.python.org/packages/source/g/groestlcoin_hash/groestlcoin_hash-{version}.tar.gz'  # noqa
    depends = ['python3crystax']
    call_hostpython_via_targetpython = True
    cythonize = False

    def get_recipe_env(self, arch):
        # Overriding the original method because we need to add the
        # libpythonX.Y location to LDFLAGS to be able to link against it
        # maybe this should be done in the super method and benefit
        # other recipes instead?
        env = super(groestlcoin_hashRecipe, self).get_recipe_env(arch)
        ndk_dir = self.ctx.ndk_dir
        python_version = '.'.join(self.ctx.python_recipe.version.split('.')[:2])
        ndk_path = os.path.join(
            ndk_dir, 'sources', 'python', python_version, 'libs', arch.arch
        )
        env['LDFLAGS'] = ' -L {}'.format(ndk_path) + env['LDFLAGS']
        return env


recipe = groestlcoin_hashRecipe()
