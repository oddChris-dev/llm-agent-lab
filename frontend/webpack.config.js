const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = (env, argv) => {
  const isDevelopment = argv.mode === 'development';

  return {
    entry: './src/index.tsx',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: isDevelopment ? '[name].js' : '[name].[contenthash].js',
      publicPath: '/',
      clean: true,
    },
    module: {
      rules: [
        {
          test: /\.tsx?$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: ['style-loader', 'css-loader', 'postcss-loader'],
        },
        {
          test: /\.(png|svg|jpg|jpeg|gif)$/i,
          type: 'asset/resource',
        },
        {
          test: /\.(woff|woff2|eot|ttf|otf)$/i,
          type: 'asset/resource',
        },
      ],
    },
    resolve: {
      extensions: ['.tsx', '.ts', '.js'],
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@hooks': path.resolve(__dirname, 'src/hooks'),
        '@stores': path.resolve(__dirname, 'src/stores'),
        '@api': path.resolve(__dirname, 'src/api'),
        '@types': path.resolve(__dirname, 'src/types'),
      },
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './public/index.html',
        title: 'LLM Agent Lab',
      }),
    ],
    devServer: {
      static: {
        directory: path.join(__dirname, 'public'),
      },
      port: 3000,
      hot: true,
      historyApiFallback: true,
      proxy: [
        {
          context: ['/api', '/ws'],
          target: 'http://localhost:8000',
          changeOrigin: true,
          ws: true,
        },
      ],
    },
    devtool: isDevelopment ? 'eval-source-map' : 'source-map',
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
          reactflow: {
            test: /[\\/]node_modules[\\/](reactflow|@reactflow)[\\/]/,
            name: 'reactflow',
            chunks: 'all',
          },
        },
      },
    },
  };
};
