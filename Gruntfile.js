module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    less: {
      css: {
        options: {
            paths: ['components/bootstrap/less/', 'components/select2-bootstrap-css/lib/']
        },
        files: {
          'public/css/lutris.css': ['common_static/css/lutris.less']
        }
      },
      min: {
        options: {
            yuicompress: true,
            paths: ['components/bootstrap/less/', 'components/select2-bootstrap-css/lib/']
        },
        files: {
            'public/css/lutris.min.css': ['common_static/css/lutris.less']
        }
      }
    },
    coffee: {
      compile: {
        files: {
          'public/js/app.js': 'common_static/js/*.coffee',
          'public/js/jcrop-fileinput.js': 'components/jcrop-fileinput/src/jcrop-fileinput.coffee'
        }
      }
    },
    concat: {
      css: {
        src: [
          'components/jcrop/css/jquery.Jcrop.css',
          'components/jcrop-fileinput/dist/jcrop-fileinput.css',
          'components/select2/select2.css',
          'components/select2-bootstrap-css/select2-bootstrap.css'
        ],
        dest: 'public/css/libs.css',
        nonull: true
      },
      js: {
        src: [
          'components/jquery/jquery.js',
          'components/modernizr/modernizr.js',
          'components/bootstrap/dist/js/bootstrap.js',
          'components/jcrop-fileinput/dist/jcrop-fileinput.js',
          'components/select2/select2.js',
        ],
        dest: 'public/js/libs.js',
        nonull: true
      }
    },
    cssmin: {
      dist: {
        files: {
          'public/css/libs.min.css': ['public/css/libs.css']
        }
      }
    },
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      dist: {
        files: {
          'public/js/libs.min.js': ['public/js/libs.js'],
          'public/js/app.min.js': ['public/js/app.js']
        }
      }
    },
    watch: {
      options: {
        livereload: true
      },
      less: {
        files: 'common_static/css/lutris.less',
        tasks: ['less:css']
      },
      coffee: {
        files: [
          'common_static/js/*.coffee',
          'components/jcrop-fileinput/src/*.coffee'
        ],
        tasks: ['coffee', 'uglify:app']
      },
      templates: {
        files: ['templates/**/*.html']
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-coffee');

  grunt.registerTask('default', ['less', 'coffee', 'concat', 'cssmin', 'uglify']);
};

