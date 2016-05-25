#!/bin/bash
set -e -x

function install_openssl {
    # Compile and parallel-install a newer OpenSSL version so that curl can
    # download from the rust servers
    pushd /usr/src
    wget -q ftp://ftp.openssl.org/source/openssl-${1}.tar.gz
    tar xf openssl-${1}.tar.gz
    cd openssl-${1}
    ./config --prefix=/opt/openssl shared > /dev/null
    make > /dev/null
    make install > /dev/null
    export LD_LIBRARY_PATH=/opt/openssl/lib:$LD_LIBRARY_PATH
    popd
}

function install_curl {
    pushd /usr/src
    # Compile an up-to-date curl version that links to our own OpenSSL installation
    wget -q --no-check-certificate http://curl.haxx.se/download/curl-${1}.tar.gz
    tar xf curl-${1}.tar.gz
    cd curl-${1}
    ./configure --with-ssl=/opt/openssl --prefix=/opt/curl > /dev/null
    make > /dev/null
    make install > /dev/null
    export PATH=/opt/curl/bin:$PATH
    popd
}

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
    find ./ -name "__pycache__" -type d -print0 |xargs rm -rf --
    find ./ -name "*.pyc" -type f -print0 |xargs rm -rf --
    popd
}

OPENSSL_VERSION=1.0.2h
CURL_VERSION=7.49.0
RUST_CHANNEL=nightly

# Clean build files
clean_project

install_openssl $OPENSSL_VERSION
install_curl $CURL_VERSION
install_rust $RUST_CHANNEL

# Remove old wheels
rm -rf /io/wheelhouse/* || echo "No old wheels to delete"

# We don't support Python 2.6
rm -rf /opt/python/cp26*

# Install libraries needed for compiling the extension
yum -q -y install libffi-devel

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    ${PYBIN}/python -m pip wheel /io/ -w /wheelhouse/
    clean_project
done

# Move pure wheels to output wheelhouse
mkdir -p /io/wheelhouse/
mv /wheelhouse/*any.whl /io/wheelhouse/ || echo "No pure wheels found."

# Bundle external shared libraries into the wheels
for whl in /wheelhouse/*.whl; do
    auditwheel repair $whl -w /io/wheelhouse/
done

# Set permissions on wheels
chmod -R a+rw /io/wheelhouse

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    ${PYBIN}/python -m pip install pytest
    ${PYBIN}/python -m pip install rust_fst --no-index -f /io/wheelhouse
    ${PYBIN}/python -m pytest --verbose /io/tests
    clean_project
done
