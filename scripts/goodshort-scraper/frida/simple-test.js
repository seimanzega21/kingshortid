/**
 * SIMPLE output - no hooks, just direct calls
 */

setTimeout(function () {
    Java.perform(function () {
        var AppUtils = Java.use('com.newreading.goodreels.utils.AppUtils');

        var ts = '1769855063192';
        var path = '/home/index';

        send('=== DIRECT TEST ===');
        send('GAID: ' + AppUtils.getGAID());
        send('AndroidID: ' + AppUtils.getAndroidID());
        send('Package: ' + AppUtils.getPkna());

        var sign = AppUtils.getSign(ts, path);
        send('SIGN: ' + sign);

        var expected = 'VTHYJWUtBYS5e0k4w/UuC3/uQnIHzRPrm7dMhdEWBnt5Uxm9DV4qxG/92PNTr6bfFTY8MiqjBmcV6gf6Bjm4xnCHEun1PU7bfROwwbGh08TiL3CjIefWBp27Uhit/gquZXk+pTn9XgyKVHtFYHGJBRgUg7Ps/etgAzVcmUdnXNP5uAg6demZORtW3Qv9iHv5Uctas4s0eV1idPafxnHGI7/FcdKItQf6ziWu4/WRQi+aM/+JF9sUO7yqD0KLTM76TIEkq8QTyGbksYHtXFA9enM3jWbaMjhts5jpI4Jb3yQQPpewMDbnbLqcKhGfvXIk4tppoYi4wx/21BIpBFW5cQ==';
        send('MATCH: ' + (sign === expected));
        send('===================');
    });
}, 3000);
