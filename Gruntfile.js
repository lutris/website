module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    copy: {
      main: {
        files: [
          {
            expand: true,
            flatten: true,
            src: ['components/bootstrap/dist/fonts/*'],
            dest: 'public/fonts/'
          }
        ]
      }
    },
    less: {
      css: {
        options: {
            paths: ['components/bootstrap/less/']
        },
        files: {
          'public/css/lutris.css': ['common_static/css/lutris.less']
        }
      },
      min: {
        options: {
            yuicompress: true,
            paths: ['components/bootstrap/less/']
        },
        files: {
            'public/css/lutris.min.css': ['common_static/css/lutris.less']
        }
      }
    },
    concat: {
      css: {
        src: [
          'components/jcrop/css/jquery.Jcrop.css',
          'components/jcrop-fileinput/dist/jcrop-fileinput.css',
          'components/select2/select2.css',
          'components/select2-bootstrap3-css/select2-bootstrap.css'
        ],
        dest: 'public/css/libs.css',
        nonull: true
      },
      app: {
        src: ['common_static/js/*.js'],
        dest: 'public/js/app.js',
        nonull: true
      },
      js: {
        src: [
          'components/jquery/dist/jquery.js',
          'components/blueimp-canvas-to-blob/js/canvas-to-blob.js',
          'components/modernizr/modernizr.js',
          'components/bootstrap/dist/js/bootstrap.js',
          'components/jcrop/js/jquery.Jcrop.js',
          'components/jcrop-fileinput/dist/jcrop-fileinput.js',
          'components/select2/select2.js'
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
      less: {
        files: 'common_static/css/lutris.less',
        tasks: ['less:css']
      },
      templates: {
        files: ['templates/**/*.html']
      }
    },
    browserSync: {
      dev: {
        bsFiles: {
          src: [
            'templates/**',
            'public/**'
          ]
        },
        options: {
          proxy: 'localhost:8000',
          watchTask: true
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-browser-sync');
  grunt.loadNpmTasks('grunt-contrib-less');

  grunt.registerTask('default', ['copy', 'less', 'concat', 'cssmin', 'uglify']);
  grunt.registerTask('serve', ['browserSync', 'watch']);
};

