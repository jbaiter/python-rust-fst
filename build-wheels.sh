#!/bin/bash
set -e -x

function install_rust {
    curl https://static.rust-lang.org/rustup.sh > /tmp/rustup.sh
    chmod +x /tmp/rustup.sh
    /tmp/rustup.sh -y --disable-sudo --channel=$1
}

function update_certificates {
    # Update the Root CA bundle
    wget -q --no-check-certificate \
        -O /etc/pki/tls/certs/ca-bundle.crt \
        http://curl.haxx.se/ca/cacert.pem
}

function clean_project {
    # Remove compiled files that might cause conflicts
    pushd /io/
    rm -rf .cache .eggs rust_fst/_ffi.py build *.egg-info
    find ./ -name "__pycache__" -type d -print0 |xargs -0 rm -rf
    find ./ -name "*.pyc" -type f -print0 |xargs -0 rm -rf
    find ./ -name "*.so" -type f -print0 |xargs -0 rm -rf
    popd
}

RUST_CHANNEL=nightly

# It doesn't matter with which Python version we build  the wheel, so we
# use the oldest supported one
if [[ $1 == "osx" ]]; then
    brew update
    brew install mmv
    pip install -U pip setuptools wheel
    install_rust $RUST_CHANNEL
    pip wheel . -w ./wheelhouse
    mmv "./wheelhouse/rust_fst-*-cp*-cp*-macosx*.whl" \
        "./wheelhouse/rust_fst-#1-py2.py3-none-macosx#4.whl"
    pip install cffi
    pip install -v rust_fst --no-index -f ./wheelhouse
    pip install -r "test-requirements.txt"
    cd ../
    py.test ./python-rust-fst/tests
else
    PYBIN=/opt/python/cp27-cp27m/bin
    # Clean build files
    clean_project

    install_rust $RUST_CHANNEL

    # Remove old wheels
    rm -rf /io/wheelhouse/* || echo "No old wheels to delete"

    # We don't support Python 2.6
    rm -rf /opt/python/cp26*

    # Install libraries needed for compiling the extension
    yum -q -y install libffi-devel mmv

    # Compile wheel
    ${PYBIN}/python -m pip wheel /io/ -w /wheelhouse/

    # Move pure wheels to target directory
    mkdir -p /io/wheelhouse
    mv /wheelhouse/*any.whl /io/wheelhouse || echo "No pure wheels to move"

    # Bundle external shared libraries into the wheel
    for whl in /wheelhouse/*.whl; do
        auditwheel repair $whl -w /io/wheelhouse/
    done

    # Rename wheels to match all Python versions
    mmv "/io/wheelhouse/rust_fst-*-cp*-cp*-manylinux1_*.whl" \
        "/io/wheelhouse/rust_fst-#1-py2.py3-none-manylinux1_#4.whl"

    # Set permissions on wheels
    chmod -R a+rw /io/wheelhouse

    # Install packages and test with all Python versions
    for PYBIN in /opt/python/*/bin/; do
        ${PYBIN}/python -m pip install cffi
        ${PYBIN}/python -m pip install -r "/io/test-requirements.txt"
        ${PYBIN}/python -m pip install rust_fst --no-index -f /io/wheelhouse
        ${PYBIN}/python -m pytest --verbose /io/tests
        clean_project
    done
fi
