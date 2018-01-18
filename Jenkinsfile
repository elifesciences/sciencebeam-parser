elifeLibrary {
    stage 'Checkout', {
        checkout scm
    }

    stage 'Build image', {
        sh 'docker build --no-cache -t elife/sciencebeam .'
    }

    stage 'Run tests', {
        elifeLocalTests './project_tests.sh'
    }
}
