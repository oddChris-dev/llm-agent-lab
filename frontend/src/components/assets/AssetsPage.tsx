/**
 * Asset management page for uploading and managing voice samples and other assets.
 */

import React, { useState, useRef } from 'react';
import {
  Upload,
  Trash2,
  Download,
  Play,
  Pause,
  Mic,
  Image,
  FileText,
  File,
  Loader2,
  X,
  Search,
} from 'lucide-react';
import { useAssets, useCreateAsset, useDeleteAsset, getAssetDownloadUrl } from '../../hooks/useAssets';
import type { Asset } from '../../api/assets';

type AssetTypeFilter = 'all' | 'voice_sample' | 'image' | 'audio' | 'document' | 'other';

const ASSET_TYPE_OPTIONS: { value: Asset['type']; label: string; icon: React.ReactNode }[] = [
  { value: 'voice_sample', label: 'Voice Sample', icon: <Mic className="w-4 h-4" /> },
  { value: 'audio', label: 'Audio', icon: <Play className="w-4 h-4" /> },
  { value: 'image', label: 'Image', icon: <Image className="w-4 h-4" /> },
  { value: 'document', label: 'Document', icon: <FileText className="w-4 h-4" /> },
  { value: 'other', label: 'Other', icon: <File className="w-4 h-4" /> },
];

const TYPE_ICONS: Record<string, React.ReactNode> = {
  voice_sample: <Mic className="w-5 h-5 text-pink-500" />,
  audio: <Play className="w-5 h-5 text-purple-500" />,
  image: <Image className="w-5 h-5 text-blue-500" />,
  document: <FileText className="w-5 h-5 text-yellow-500" />,
  video: <Play className="w-5 h-5 text-red-500" />,
  other: <File className="w-5 h-5 text-gray-500" />,
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AssetsPage() {
  const [typeFilter, setTypeFilter] = useState<AssetTypeFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [playingAssetId, setPlayingAssetId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { data: assets, isLoading, error } = useAssets(
    typeFilter === 'all' ? undefined : typeFilter
  );
  const deleteAsset = useDeleteAsset();

  // Filter assets by search query
  const filteredAssets = assets?.filter((asset) =>
    asset.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDelete = (asset: Asset) => {
    if (window.confirm(`Are you sure you want to delete "${asset.name}"?`)) {
      deleteAsset.mutate(asset.id);
    }
  };

  const handlePlay = (asset: Asset) => {
    if (playingAssetId === asset.id) {
      // Stop playing
      audioRef.current?.pause();
      setPlayingAssetId(null);
    } else {
      // Play this asset
      if (audioRef.current) {
        audioRef.current.src = getAssetDownloadUrl(asset.id);
        audioRef.current.play();
        setPlayingAssetId(asset.id);
      }
    }
  };

  const handleAudioEnded = () => {
    setPlayingAssetId(null);
  };

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">Failed to load assets. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hidden audio element for playback */}
      <audio ref={audioRef} onEnded={handleAudioEnded} />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Assets
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Manage voice samples, images, and other assets
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
        >
          <Upload className="w-5 h-5" />
          Upload Asset
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search assets..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
          />
        </div>

        {/* Type filter */}
        <div className="flex gap-2">
          <button
            onClick={() => setTypeFilter('all')}
            className={`px-3 py-2 text-sm rounded-lg transition-colors ${
              typeFilter === 'all'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            All
          </button>
          {ASSET_TYPE_OPTIONS.slice(0, 3).map((opt) => (
            <button
              key={opt.value}
              onClick={() => setTypeFilter(opt.value)}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg transition-colors ${
                typeFilter === opt.value
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {opt.icon}
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Assets Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        </div>
      ) : filteredAssets?.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-200 dark:border-gray-700">
          <File className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            {searchQuery
              ? 'No assets match your search'
              : 'No assets yet. Upload your first one!'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              <Upload className="w-5 h-5" />
              Upload Asset
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAssets?.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              isPlaying={playingAssetId === asset.id}
              onPlay={handlePlay}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadAssetModal onClose={() => setShowUploadModal(false)} />
      )}
    </div>
  );
}

interface AssetCardProps {
  asset: Asset;
  isPlaying: boolean;
  onPlay: (asset: Asset) => void;
  onDelete: (asset: Asset) => void;
}

function AssetCard({ asset, isPlaying, onPlay, onDelete }: AssetCardProps) {
  const isAudio = asset.type === 'voice_sample' || asset.type === 'audio';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
          {TYPE_ICONS[asset.type] || TYPE_ICONS.other}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 dark:text-white truncate">
            {asset.name}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {asset.type_display} • {formatFileSize(asset.file_size)}
          </p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-gray-400">
          {formatDate(asset.created_at)}
        </span>
        <div className="flex items-center gap-1">
          {isAudio && (
            <button
              onClick={() => onPlay(asset)}
              className={`p-1.5 rounded transition-colors ${
                isPlaying
                  ? 'text-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'text-gray-400 hover:text-primary-500'
              }`}
              title={isPlaying ? 'Stop' : 'Play'}
            >
              {isPlaying ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
            </button>
          )}
          <a
            href={getAssetDownloadUrl(asset.id)}
            download={asset.name}
            className="p-1.5 text-gray-400 hover:text-blue-500 rounded transition-colors"
            title="Download"
          >
            <Download className="w-4 h-4" />
          </a>
          <button
            onClick={() => onDelete(asset)}
            className="p-1.5 text-gray-400 hover:text-red-500 rounded transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

interface UploadAssetModalProps {
  onClose: () => void;
}

function UploadAssetModal({ onClose }: UploadAssetModalProps) {
  const createAsset = useCreateAsset();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [name, setName] = useState('');
  const [type, setType] = useState<Asset['type']>('voice_sample');
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      if (!name) {
        setName(e.dataTransfer.files[0].name);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      if (!name) {
        setName(e.target.files[0].name);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    try {
      await createAsset.mutateAsync({
        file,
        name: name || file.name,
        type,
      });
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to upload asset');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Upload Asset
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg">
              {error}
            </div>
          )}

          {/* File Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              dragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : file
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileChange}
              className="hidden"
              accept=".mp3,.wav,.ogg,.flac,.m4a,.png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.md"
            />
            {file ? (
              <div>
                <File className="w-10 h-10 text-green-500 mx-auto mb-2" />
                <p className="text-sm text-gray-900 dark:text-white font-medium">
                  {file.name}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatFileSize(file.size)}
                </p>
              </div>
            ) : (
              <div>
                <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Drag & drop a file here, or click to browse
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Max file size: 100MB
                </p>
              </div>
            )}
          </div>

          {/* Name */}
          <div>
            <label
              htmlFor="assetName"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Asset Name
            </label>
            <input
              type="text"
              id="assetName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Voice Sample"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Asset Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              {ASSET_TYPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setType(opt.value)}
                  className={`inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors ${
                    type === opt.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                      : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  {opt.icon}
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createAsset.isPending || !file}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {createAsset.isPending && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              {createAsset.isPending ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
