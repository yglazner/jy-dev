"""Naval Fate.

Usage:
  jy_dev new
  jy_dev update
  jy_dev jar
  jy_dev (-h | --help)
  jy_dev --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.

"""
from __future__ import with_statement
'''
Created on Apr 3, 2014

@author: yoav glazner
'''

import os, sys
import shutil
import zipfile
import time


class OutOfCheeseError(Exception):
    pass

def get_deps():
    outdir = 'target/dependency'
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir)
    print 'trying to get IVY'
    if not os.path.exists('ivy-2.3.0.jar'):
        print 'try to get ivy'
	res = os.system('curl -O http://search.maven.org/remotecontent?filepath=org/apache/ivy/ivy/2.3.0/ivy-2.3.0.jar')
    assert os.path.isfile('ivy-2.3.0.jar'), 'couldn\'t get IVY'
    with open('deps.txt', 'r') as f:
        deps = [line.split() for line in f if line.strip()]
    for groupId, artifactId, version in deps:
        print 'trying to get', groupId, artifactId, version
        
        ret = os.system('java -jar ivy-2.3.0.jar -dependency %s %s %s -retrieve "%s/[artifact]-[revision](-[classifier]).[ext]"'%
                        (groupId, artifactId, version, outdir))
        if ret:
            print 'blarrrg got ', ret, 'from the evil maven...'
            raise OutOfCheeseError('Blash Maven died')
       
    time.sleep(1)#stdout vs stderr race...
    print 'Yay! now fix your project includes! =P'

def make_jar(jar_name=None):
    
    if not jar_name:
        jar_name = os.path.split(os.path.abspath('.'))[-1].replace('\\', '').replace('/', '')
    OUTPUT = 'target/%s.jar' % jar_name
    if not os.path.exists('target'):
        os.makedirs('target')
#     os.remove(OUTPUT)
    jython_home = os.getenv('JYTHON_HOME', '/home/local/jython2.5.3/')
    shutil.copy(os.path.join(jython_home, 'jython.jar'), OUTPUT)
    copy_jars('./target/dependency', OUTPUT)
    zipper(os.path.join(jython_home, 'Lib'), OUTPUT, 'Lib/')
    #zipper('./target/dependency', OUTPUT, 'dependency', add_to_manifest=True)
    zipper('./src', OUTPUT)
    
    with open('target/run.sh', 'w') as f:
        f.write('java -cp %s.jar org.python.util.jython -jar %s.jar' % (jar_name, jar_name))
    print '_' * 100
    print 'DONE!'



def copy_jars(jars_path , OUTPUT):
    dst = os.path.join(jars_path, 'extracted')
    if os.path.exists(dst):
        shutil.rmtree(dst)
    for jar_file in os.listdir(jars_path):
        if jar_file[-3:].lower() != 'jar': continue
        
        if 'sources.jar' in jar_file or '-javadoc.jar' in jar_file:
            print 'skiping useless stuff', jar_file
        
        zip = zipfile.ZipFile(os.path.join(jars_path, jar_file))
        
        print 'found jar:', jar_file
        for name in zip.namelist():
            
            if name.upper().startswith('META-INF'): continue
            print 'extracting:', name
            folder, filename = os.path.split(name)
            if not filename:
                folder = os.path.join(dst,folder)
                if not os.path.exists(folder):
                    os.makedirs(folder)
            else:
                fd = open(os.path.join(dst, name), 'w')
                fd.write(zip.read(name))
                fd.close()
        zip.close()
    zipper(dst, OUTPUT)

        
def zipper(dir, zip_file, nested_folder=False):
    zip = zipfile.ZipFile(zip_file, 'a', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(dir))
    if nested_folder:
        root_len -= 1+len(os.path.split(dir)[-1])
    for root, dirs, files in os.walk(dir):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            print 'copying ->', f ,' to:', archive_name
            zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
           
    zip.close()
    return zip_file


def new_project():
    project_name = os.path.split(os.path.abspath('.'))[-1].replace('\\', '').replace('/', '')
    s = '''<?xml version="1.0" encoding="UTF-8"?>
    <?eclipse-pydev version="1.0"?>
    <pydev_project>
        <pydev_property name="org.python.pydev.PYTHON_PROJECT_INTERPRETER">Default</pydev_property>
        <pydev_property name="org.python.pydev.PYTHON_PROJECT_VERSION">jython 2.5</pydev_property>
        <pydev_variables_property name="org.python.pydev.PROJECT_VARIABLE_SUBSTITUTION">
        </pydev_variables_property>
        <pydev_pathproperty name="org.python.pydev.PROJECT_SOURCE_PATH">
            <path>/%s/src</path>
            <path>/%s/ut</path>
        </pydev_pathproperty>
    </pydev_project>

        ''' % (project_name, project_name)
        
    with open('.pydevproject', 'w') as f:
        f.write(s)
        
    
        
    s = '''<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
  <name>%s</name>
  <comment>NO_M2ECLIPSE_SUPPORT: Project files created with the maven-eclipse-plugin are not supported in M2Eclipse.</comment>
  <projects/>
  <buildSpec>
    <buildCommand>
      <name>org.python.pydev.PyDevBuilder</name>
    </buildCommand>
    <buildCommand>
      <name>org.eclipse.jdt.core.javabuilder</name>
    </buildCommand>
  </buildSpec>
  <natures>
    <nature>org.python.pydev.pythonNature</nature>
    <nature>org.eclipse.jdt.core.javanature</nature>
  </natures>
</projectDescription>

    ''' % (project_name, )
    with open('.project', 'w') as f:
        f.write(s)
    s = '''\
org.mongodb mongo-java-driver 2.11.4'''
    with open('deps.txt', 'w') as f:
        f.write(s)
        
    for dir in ['src', 'ut']:
        if not os.path.exists(dir):
            os.makedirs(dir)
    if not os.path.exists('src/__run__.py'):
        with open('src/__run__.py', 'w') as f:
            f.write('''"""This is your main app file
            """
            print ("hello world with jy_dev!!!")
            ''')


def main():
    from jy_dev import docopt
    options = docopt.docopt(__doc__, version='jy_dev 0.1a')
    
    print(options)
   
    if options['new']:
        print 'yay got new'
        new_project()
    elif options['jar']:
        make_jar()
    elif options['update']:
        get_deps()
    
    print 'bye bye'
                
    

if __name__ == '__main__':
    if len(sys.argv)==1:
        sys.argv.append('update')
    main()
