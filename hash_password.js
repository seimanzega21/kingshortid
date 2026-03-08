const bcrypt = require("bcryptjs");
bcrypt.hash("Radhika05@", 10).then(h => {
    console.log(h);
    process.exit(0);
});
